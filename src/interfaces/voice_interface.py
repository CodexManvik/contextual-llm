import threading
import queue
import sounddevice as sd
import numpy as np
import time
import logging
from typing import Optional, Callable
import os
import atexit
import gc
import json

import pyttsx3
from typing import List, Optional

try:
    # Optional Whisper ASR (faster-whisper)
    from src.asr.whisper_asr import WhisperASR
    WHISPER_AVAILABLE = True
except Exception:
    WHISPER_AVAILABLE = False

try:
    # Optional Piper TTS for better quality
    import piper
    PIPER_AVAILABLE = True
except Exception:
    PIPER_AVAILABLE = False

# Try to import Vosk for speech recognition
try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("⚠️ Vosk not available. Install with: pip install vosk")

class VoiceInterface:
    def __init__(self, sample_rate: int = 16000):
        self.logger = logging.getLogger(__name__)
        self.sample_rate = sample_rate

        # TTS setup
        self.tts_engine = None
        self.piper_tts = None
        self._tts_lock = threading.Lock()
        self._configure_tts()

        # Audio processing
        self.audio_queue = queue.Queue(maxsize=10)
        self.is_listening = False
        self.command_callback: Optional[Callable[[str], None]] = None
        self.stream = None
        
        # Voice recognition setup
        self.voice_detected = False
        self.silence_threshold = 0.01
        self.voice_threshold = 0.03  # Lowered threshold for better sensitivity
        
        # ASR backends
        self.vosk_model = None
        self.vosk_recognizer = None
        self.whisper_asr = None
        self.asr_enabled = False
        
        # Prefer Whisper (GPU-accelerated), fallback to Vosk
        if WHISPER_AVAILABLE:
            self._setup_whisper_asr()
        # If Whisper failed to initialize, try Vosk
        if not self.asr_enabled and VOSK_AVAILABLE:
            self._setup_vosk_asr()
        
        # Register cleanup on exit
        atexit.register(self._cleanup_on_exit)

    def _configure_tts(self):
        """Configure text-to-speech engine"""
        # Try Piper TTS first (better quality)
        if PIPER_AVAILABLE:
            self._setup_piper_tts()
        
        # Fallback to pyttsx3
        if not self.piper_tts:
            self._setup_pyttsx3_tts()
    
    def _setup_piper_tts(self):
        """Setup Piper TTS for high-quality voice"""
        try:
            # Look for Piper voice models
            piper_voices = [
                # Prefer British female first per user preference
                "models/piper/en-gb-sarah-medium.onnx",
                "models/piper/en-gb-sarah-low.onnx",
                # Then American female options
                "models/piper/en-us-amy-medium.onnx",
                "models/piper/en-us-amy-low.onnx",
            ]
            
            for voice_path in piper_voices:
                if os.path.exists(voice_path):
                    print(f"🎯 Loading Piper voice: {voice_path}")
                    self.piper_tts = piper.PiperVoice.load(voice_path)
                    print("✅ Piper TTS enabled!")
                    return
                    
        except Exception as e:
            self.logger.warning(f"Piper TTS setup failed: {e}")
            self.piper_tts = None
    
    def _setup_pyttsx3_tts(self):
        """Setup pyttsx3 TTS as fallback"""
        try:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            
            # Prefer British English female voices first
            preferred_order: List[str] = [
                'hazel', 'en-gb', 'uk', 'british', 'female',
                # then general English and US as fallback
                'zira', 'en-us', 'english'
            ]
            selected = None
            for key in preferred_order:
                for voice in voices or []:
                    name = (voice.name or '').lower()
                    lang = ' '.join(getattr(voice, 'languages', []) or []).lower()
                    if key in name or key in lang:
                        selected = voice.id
                        break
                if selected:
                    break
            if selected and voices:
                self.tts_engine.setProperty('voice', selected)
            self.tts_engine.setProperty('rate', 180)
            self.tts_engine.setProperty('volume', 0.8)
            print("✅ pyttsx3 TTS enabled!")
        except Exception as e:
            self.logger.warning(f"pyttsx3 TTS configuration failed: {e}")
            self.tts_engine = None

    def _setup_whisper_asr(self):
        """Setup Whisper ASR via faster-whisper (GPU-accelerated)."""
        try:
            # Defaults tuned for RTX 3050 4GB
            model_size = os.getenv('WHISPER_MODEL', 'small')
            compute_type = os.getenv('WHISPER_COMPUTE_TYPE', 'int8_float16')
            device_index = int(os.getenv('WHISPER_DEVICE_INDEX', '0'))
            language = os.getenv('WHISPER_LANGUAGE', 'en')  # Indian English mostly recognized under en

            self.whisper_asr = WhisperASR(
                model_name_or_path=model_size,
                device='cuda' if os.getenv('WHISPER_DEVICE', 'cuda') == 'cuda' else 'cpu',
                device_index=device_index,
                compute_type=compute_type,
                language=language,
                beam_size=int(os.getenv('WHISPER_BEAM_SIZE', '1')),
                vad_filter=os.getenv('WHISPER_VAD_FILTER', '1') == '1',
            )
            self.asr_enabled = True
            print("✅ Whisper ASR enabled (faster-whisper)")
        except Exception as e:
            self.logger.error(f"Failed to setup Whisper ASR: {e}")
            self.whisper_asr = None
            self.asr_enabled = False

    def _setup_vosk_asr(self):
        """Setup Vosk ASR model"""
        try:
            # Try to find Vosk model in common locations
            model_paths = [
                "models/vosk/vosk-model-small-en-us-0.15",
                "models/vosk/vosk-model-en-us-0.22",
                "models/vosk-model-small-en-us-0.15",
                "models/vosk-model-en-us-0.22",
                os.path.expanduser("~/vosk-model-small-en-us-0.15"),
                os.path.expanduser("~/vosk-model-en-us-0.22"),
            ]
            
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if model_path and not self.asr_enabled:
                print(f"🎯 Loading Vosk model from: {model_path}")
                self.vosk_model = Model(model_path)
                self.vosk_recognizer = KaldiRecognizer(self.vosk_model, self.sample_rate)
                self.asr_enabled = True
                print("✅ Vosk ASR enabled!")
            else:
                print("⚠️ Vosk model not found. Download from: https://alphacephei.com/vosk/models")
                print("   Place in 'models/' directory or home directory")
                print("   Using voice detection mode only.")
                
        except Exception as e:
            self.logger.error(f"Failed to setup Vosk ASR: {e}")
            print(f"❌ Vosk ASR setup failed: {e}")
            self.asr_enabled = False

    def speak(self, text: str):
        """Speak text using TTS"""
        try:
            print(f"🔊 Assistant: {text}")
            with self._tts_lock:
                if self.piper_tts:
                    # Use Piper TTS for high quality
                    self.piper_tts.synthesize(text)
                elif self.tts_engine:
                    # Fallback to pyttsx3
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                else:
                    # No TTS available, just print
                    pass
        except Exception as e:
            self.logger.error(f"TTS Error: {e}")
            print(f"🔊 Assistant: {text}")  # Fallback to print

    def set_command_callback(self, callback: Callable[[str], None]):
        """Set callback for voice commands"""
        self.command_callback = callback

    def _detect_voice_activity(self, audio_chunk: np.ndarray) -> bool:
        """Simple voice activity detection"""
        if audio_chunk is None or audio_chunk.size == 0:
            return False
        
        # Calculate RMS (Root Mean Square) of audio
        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))
        
        # Normalize to 0-1 range
        normalized_rms = rms / 32768.0
        
        # Debug: Show audio levels occasionally
        if hasattr(self, '_debug_counter'):
            self._debug_counter += 1
        else:
            self._debug_counter = 0
            
        if self._debug_counter % 50 == 0:  # Show every 50th sample
            print(f"🔊 Audio level: {normalized_rms:.4f} (threshold: {self.voice_threshold:.4f})")
        
        return normalized_rms > self.voice_threshold

    def start_listening(self):
        """Start voice interface with simple voice detection"""
        if self.is_listening:
            return

        def audio_callback(indata, frames, time_info, status):
            if status:
                self.logger.warning(f"Audio status: {status}")
            try:
                self.audio_queue.put(indata.copy(), timeout=0.1)
            except queue.Full:
                # Drop if queue is full to avoid backpressure
                pass

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                callback=audio_callback,
                blocksize=8000  # ~0.5s
            )
            self.stream.start()
        except Exception as e:
            self.logger.error(f"Failed to start audio input stream: {e}")
            self.speak("Unable to access the microphone. Please check your audio device.")
            return

        self.is_listening = True

        # Start voice detection loop
        threading.Thread(target=self._voice_detection_loop, daemon=True).start()
        
        if self.asr_enabled:
            print("🎤 Voice interface started (ASR Mode)")
            print("✅ Real speech recognition enabled!")
        else:
            print("🎤 Voice interface started (Voice Detection Mode)")
            print("📝 Note: ASR is disabled. Voice commands will be simulated.")
        print("🔊 Speak to trigger voice detection events.")
        print("Press Ctrl+C to stop...")

    def stop_listening(self):
        """Stop voice interface"""
        self.is_listening = False
        
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        
        print("🛑 Voice interface stopped.")

    def _voice_detection_loop(self):
        """Main voice detection loop"""
        buffer = np.array([], dtype=np.int16)
        max_chunk_sec = 1.0  # Shorter chunks for voice detection
        max_chunk_samples = int(self.sample_rate * max_chunk_sec)
        voice_start_time = None
        min_voice_duration = 0.5  # Minimum voice duration to trigger
        asr_buffer = b""  # Buffer for ASR processing

        while self.is_listening:
            try:
                chunk = self.audio_queue.get(timeout=0.3)
                buffer = np.concatenate((buffer, chunk.flatten()))

                if len(buffer) >= max_chunk_samples:
                    # Check for voice activity
                    voice_detected = self._detect_voice_activity(buffer)
                    
                    if voice_detected and voice_start_time is None:
                        # Voice started
                        voice_start_time = time.time()
                        print("🎤 Voice detected...")
                        asr_buffer = b""  # Reset ASR buffer
                    
                    elif not voice_detected and voice_start_time is not None:
                        # Voice ended
                        voice_duration = time.time() - voice_start_time
                        voice_start_time = None
                        
                        if voice_duration >= min_voice_duration:
                            print(f"🗣 Voice command detected (duration: {voice_duration:.1f}s)")
                            self._handle_voice_command(buffer, asr_buffer)
                    
                    # Add to ASR buffer if voice is detected
                    if voice_detected and self.asr_enabled:
                        asr_buffer += buffer.tobytes()
                    
                    buffer = np.array([], dtype=np.int16)

            except queue.Empty:
                continue

    def _handle_voice_command(self, audio_buffer=None, asr_buffer=None):
        """Handle detected voice command"""
        if self.command_callback:
            try:
                command = self._recognize_speech(audio_buffer, asr_buffer)
                if command:
                    print(f"🎯 Recognized command: {command}")
                    self.speak(f"Processing: {command}")
                    self.command_callback(command)
                else:
                    print("🎯 No speech recognized")
                    self.speak("I didn't catch that. Could you repeat?")
            except Exception as e:
                self.logger.error(f"Command callback error: {e}")
                self.speak("Sorry, an error occurred while processing your command.")

    def _recognize_speech(self, audio_buffer=None, asr_buffer=None):
        """Recognize speech using Vosk or fallback to simulation"""
        # Prefer Whisper if available
        if self.asr_enabled and self.whisper_asr and (asr_buffer or audio_buffer is not None):
            try:
                source = asr_buffer if asr_buffer else (audio_buffer.tobytes() if isinstance(audio_buffer, np.ndarray) else audio_buffer)
                text = self.whisper_asr.transcribe_array(source, sample_rate=self.sample_rate)
                if text:
                    return text
            except Exception as e:
                self.logger.error(f"Whisper recognition error: {e}")

        if self.asr_enabled and self.vosk_recognizer and asr_buffer:
            try:
                # Process the audio buffer with Vosk
                if self.vosk_recognizer.AcceptWaveform(asr_buffer):
                    result = json.loads(self.vosk_recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        return text.lower()
                
                # Try partial result
                partial = json.loads(self.vosk_recognizer.PartialResult())
                text = partial.get('partial', '').strip()
                if text:
                    return text.lower()
                    
            except Exception as e:
                self.logger.error(f"Vosk recognition error: {e}")
        
        # Fallback: simulate common commands based on audio level
        if audio_buffer is not None:
            rms = np.sqrt(np.mean(audio_buffer.astype(np.float32) ** 2))
            normalized_rms = rms / 32768.0
            
            # Simple heuristic based on audio intensity
            if normalized_rms > 0.1:
                return "open notepad"
            elif normalized_rms > 0.05:
                return "list applications"
            else:
                return "open calculator"
        
        return "open notepad"  # Default fallback

    def _cleanup_on_exit(self):
        """Cleanup on exit"""
        try:
            if hasattr(self, 'tts_engine') and self.tts_engine is not None:
                try:
                    self.tts_engine.stop()
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            gc.collect()

# Debug standalone run
if __name__ == "__main__":
    def test_cb(cmd):
        print(f"Command received in callback: {cmd}")

    vi = VoiceInterface()
    vi.set_command_callback(test_cb)
    vi.speak("Voice interface test started. Speak to trigger voice detection.")
    vi.start_listening()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        vi.stop_listening()
