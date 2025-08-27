import threading
import queue
import sounddevice as sd
import numpy as np
import time
import logging
from typing import Optional, Callable, List, Any, Deque
import os
import atexit
import gc
import json
from collections import deque

import pyttsx3

# ASR modules with safe imports
try:
    from asr.whisper_asr import WhisperASR
    WHISPER_AVAILABLE = True
except Exception:
    WhisperASR = None
    WHISPER_AVAILABLE = False

# Piper TTS modules with safe imports
try:
    import piper
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    piper = None
    PiperVoice = None
    PIPER_AVAILABLE = False
except Exception as e:
    print(f"Warning: Failed to import piper: {e}")
    piper = None
    PiperVoice = None
    PIPER_AVAILABLE = False

# Vosk ASR modules with safe imports
try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    Model = None
    KaldiRecognizer = None
    VOSK_AVAILABLE = False
    print("⚠️ Vosk not available. Install with: pip install vosk")

class VoiceInterface:
    def __init__(self, sample_rate: int = 16000):
        self.logger = logging.getLogger(__name__)
        self.sample_rate = sample_rate
        
        # Load configuration
        self.config = self._load_config()

        # TTS setup with type hints
        self.tts_engine: Optional[Any] = None
        self.piper_tts: Optional[Any] = None
        self._tts_lock = threading.Lock()
        self._configure_tts()

        # Audio processing
        self.audio_queue: queue.Queue = queue.Queue(maxsize=20)
        self.is_listening = False
        self.command_callback: Optional[Callable[[str], None]] = None
        self.stream: Optional[Any] = None
        
        # Voice recognition setup with improved parameters
        self.voice_detected = False
        voice_config = self.config.get('voice_interface', {})
        self.silence_threshold = voice_config.get('silence_threshold', 0.01)
        self.voice_threshold = voice_config.get('voice_threshold', 0.1)
        self.min_voice_duration = voice_config.get('min_voice_duration', 0.3)
        self.max_voice_duration = voice_config.get('max_voice_duration', 10.0)
        
        # Adaptive threshold system with type hints
        self.adaptive_threshold = self.voice_threshold
        self.background_levels: Deque[float] = deque(maxlen=100)
        self.voice_levels: Deque[float] = deque(maxlen=50)
        
        # Voice detection state
        self.voice_start_time: Optional[float] = None
        self.last_voice_time = 0.0
        self.silence_duration = 0.0
        self.voice_duration = 0.0
        
        # ASR backends with type hints
        self.vosk_model: Optional[Any] = None
        self.vosk_recognizer: Optional[Any] = None
        self.whisper_asr: Optional[Any] = None
        self.asr_enabled = False
        
        # Debug counter for logging
        self._debug_counter = 0
        
        # Initialize ASR systems
        self._initialize_asr_systems()
        
        # Register cleanup on exit
        atexit.register(self._cleanup_on_exit)

    def _initialize_asr_systems(self) -> None:
        """Initialize ASR systems with priority: Whisper -> Vosk"""
        if WHISPER_AVAILABLE:
            self._setup_whisper_asr()
        
        if not self.asr_enabled and VOSK_AVAILABLE:
            print("🔄 Whisper ASR failed, falling back to Vosk...")
            self._setup_vosk_asr()
        
        if not self.asr_enabled:
            print("❌ No ASR system available. Please install faster-whisper or vosk.")
            print("   Install faster-whisper: pip install faster-whisper")
            print("   Install vosk: pip install vosk")

    def _load_config(self) -> dict:
        """Load configuration from settings.json with proper typing"""
        config_path = "config/settings.json"
        default_config = {
            "asr": {
                "default_system": "whisper",
                "fallback_system": "vosk",
                "whisper": {
                    "model": "small",
                    "device": "cuda",
                    "compute_type": "int8_float16",
                    "language": "en",
                    "beam_size": 1,
                    "vad_filter": True
                },
                "vosk": {
                    "model_paths": []
                }
            },
            "voice_interface": {
                "sample_rate": 16000,
                "voice_threshold": 0.1,
                "silence_threshold": 0.01,
                "min_voice_duration": 0.3,
                "max_voice_duration": 10.0,
                "adaptive_threshold": True,
                "noise_reduction": True
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return self._merge_configs(default_config, config)
            else:
                print(f"⚠️ Configuration file not found: {config_path}")
                print("   Using default settings")
                return default_config
        except Exception as e:
            self.logger.warning(f"Failed to load config: {e}")
            return default_config
    
    def _merge_configs(self, default: dict, user: dict) -> dict:
        """Merge user config with defaults"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def _configure_tts(self) -> None:
        """Configure text-to-speech engine"""
        if PIPER_AVAILABLE:
            self._setup_piper_tts()
        
        if not self.piper_tts:
            self._setup_pyttsx3_tts()
    
    def _setup_piper_tts(self) -> None:
        """Setup Piper TTS for high-quality voice"""
        if not PIPER_AVAILABLE or piper is None or PiperVoice is None:
            print("⚠️ Piper not available")
            return
        
        try:
            piper_voices = [
                "models/piper/en_GB-cori-high.onnx",
                "en_GB-cori-high.onnx",
            ]
        
            for voice_path in piper_voices:
                if os.path.exists(voice_path):
                    print(f"🎯 Loading Piper voice: {voice_path}")
                    self.piper_tts = PiperVoice.load(voice_path)
                    print("✅ Piper TTS enabled!")
                    return
                
        except Exception as e:
            self.logger.warning(f"Piper TTS setup failed: {e}")
            self.piper_tts = None
    
    def _setup_pyttsx3_tts(self) -> None:
        """Setup pyttsx3 TTS as fallback"""
        try:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
        
            # Ensure voices is iterable and handle None case
            if voices is None:
                voices = []
            elif not hasattr(voices, '__iter__'):
                print("⚠️ Voices property is not iterable")
                voices = []
            else:
                # Convert to list to ensure it's iterable
                voices = list(voices)
        
            # Prefer British English female voices first
            preferred_order: List[str] = [
                'hazel', 'en-gb', 'uk', 'british', 'female',
                'zira', 'en-us', 'english'
            ]
        
            selected = None
            for key in preferred_order:
                for voice in voices:
                    if hasattr(voice, 'name') and hasattr(voice, 'id'):
                        name = (voice.name or '').lower()
                        languages = getattr(voice, 'languages', None)
                        if languages is None:
                            languages = []
                        elif isinstance(languages, str):
                            languages = [languages]
                        elif not hasattr(languages, '__iter__'):
                            languages = []
                        
                        lang = ' '.join(str(lang) for lang in languages).lower()
                        if key in name or key in lang:
                            selected = voice.id
                            break
                if selected:
                    break
                
            if selected:
                self.tts_engine.setProperty('voice', selected)
        
            self.tts_engine.setProperty('rate', 180)
            self.tts_engine.setProperty('volume', 0.8)
            print("✅ pyttsx3 TTS enabled!")
        
        except Exception as e:
            self.logger.warning(f"pyttsx3 TTS configuration failed: {e}")
            self.tts_engine = None

    def _setup_whisper_asr(self) -> None:
        """Setup Whisper ASR via faster-whisper"""
        if not WHISPER_AVAILABLE or WhisperASR is None:
            return
            
        try:
            whisper_config = self.config.get('asr', {}).get('whisper', {})
            model_size = os.getenv('WHISPER_MODEL', whisper_config.get('model', 'small'))
            compute_type = os.getenv('WHISPER_COMPUTE_TYPE', whisper_config.get('compute_type', 'int8'))
            device_index = int(os.getenv('WHISPER_DEVICE_INDEX', '0'))
            language = os.getenv('WHISPER_LANGUAGE', whisper_config.get('language', 'en'))
            beam_size = int(os.getenv('WHISPER_BEAM_SIZE', str(whisper_config.get('beam_size', 1))))
            vad_filter = os.getenv('WHISPER_VAD_FILTER', '1' if whisper_config.get('vad_filter', True) else '0') == '1'
            device = os.getenv('WHISPER_DEVICE', whisper_config.get('device', 'cpu'))

            print(f"🎯 Initializing Whisper ASR with model: {model_size}")
            self.whisper_asr = WhisperASR(
                model_name_or_path=model_size,
                device=device,
                device_index=device_index,
                compute_type=compute_type,
                language=language,
                beam_size=beam_size,
                vad_filter=vad_filter,
            )
            self.asr_enabled = True
            print("✅ Whisper ASR enabled (faster-whisper) - Default ASR System")
        except Exception as e:
            self.logger.error(f"Failed to setup Whisper ASR: {e}")
            print(f"❌ Whisper ASR setup failed: {e}")
            self.whisper_asr = None
            self.asr_enabled = False

    def _setup_vosk_asr(self) -> None:
        """Setup Vosk ASR model"""
        if not VOSK_AVAILABLE or Model is None or KaldiRecognizer is None:
            return
            
        try:
            vosk_config = self.config.get('asr', {}).get('vosk', {})
            config_paths = vosk_config.get('model_paths', [])
            
            model_paths = config_paths + [
                "models/vosk/vosk-model-en-us-0.22",
                "models/vosk/vosk-model-small-en-us-0.15",
                "models/vosk/vosk-model-en-in-0.5"
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
                print("✅ Vosk ASR enabled! (Fallback System)")
            else:
                print("⚠️ Vosk model not found. Download from: https://alphacephei.com/vosk/models")
                print("   Place in 'models/' directory")
                
        except Exception as e:
            self.logger.error(f"Failed to setup Vosk ASR: {e}")
            print(f"❌ Vosk ASR setup failed: {e}")
            self.asr_enabled = False

    def speak(self, text: str) -> None:
        """Speak text using TTS"""
        try:
            print(f"🔊 Assistant: {text}")
            with self._tts_lock:
                if self.piper_tts is not None:
                    self.piper_tts.synthesize(text)
                elif self.tts_engine is not None:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                else:
                    pass  # No TTS available, just print
        except Exception as e:
            self.logger.error(f"TTS Error: {e}")
            print(f"🔊 Assistant: {text}")

    def set_command_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for voice commands"""
        self.command_callback = callback

    def _calculate_adaptive_threshold(self) -> float:
        """Calculate adaptive threshold based on background noise"""
        if len(self.background_levels) < 10:
            return self.voice_threshold
        
        background_mean = float(np.mean(list(self.background_levels)))
        background_std = float(np.std(list(self.background_levels)))
        
        adaptive_threshold = background_mean + (2 * background_std) + 0.02
        return max(0.05, min(0.3, adaptive_threshold))

    def _detect_voice_activity(self, audio_chunk: np.ndarray) -> bool:
        """Improved voice activity detection with adaptive threshold"""
        if audio_chunk is None or audio_chunk.size == 0:
            return False
        
        rms = float(np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2)))
        normalized_rms = rms / 32768.0
        
        if not self.voice_detected:
            self.background_levels.append(normalized_rms)
        
        if self.config.get('voice_interface', {}).get('adaptive_threshold', True):
            current_threshold = self._calculate_adaptive_threshold()
        else:
            current_threshold = self.voice_threshold
        
        self._debug_counter += 1
        if self._debug_counter % 100 == 0:
            background_mean = float(np.mean(list(self.background_levels))) if self.background_levels else 0.0
            print(f"🔊 Audio: {normalized_rms:.4f} | Threshold: {current_threshold:.4f} | Background: {background_mean:.4f}")
        
        voice_detected = normalized_rms > current_threshold
        
        if voice_detected:
            self.voice_levels.append(normalized_rms)
        
        return voice_detected

    def start_listening(self) -> None:
        """Start voice interface with improved voice detection"""
        if self.is_listening:
            return

        def audio_callback(indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
            if status:
                self.logger.warning(f"Audio status: {status}")
            try:
                self.audio_queue.put(indata.copy(), timeout=0.1)
            except queue.Full:
                pass

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                callback=audio_callback,
                blocksize=4000
            )
            self.stream.start()
        except Exception as e:
            self.logger.error(f"Failed to start audio input stream: {e}")
            self.speak("Unable to access the microphone. Please check your audio device.")
            return

        self.is_listening = True
        threading.Thread(target=self._voice_detection_loop, daemon=True).start()
        
        if self.asr_enabled:
            if self.whisper_asr is not None:
                print("🎤 Voice interface started (Whisper ASR Mode)")
                print("✅ OpenAI Whisper ASR enabled as default system!")
            elif self.vosk_recognizer is not None:
                print("🎤 Voice interface started (Vosk ASR Mode)")
                print("✅ Vosk ASR enabled as fallback system!")
        else:
            print("🎤 Voice interface started (Voice Detection Mode)")
            print("📝 Note: ASR is disabled. Voice commands will be simulated.")
        
        print("🔊 Speak to trigger voice detection events.")
        print("Press Ctrl+C to stop...")

    def stop_listening(self) -> None:
        """Stop voice interface"""
        self.is_listening = False
        
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        
        print("🛑 Voice interface stopped.")

    def _voice_detection_loop(self) -> None:
        """Improved voice detection loop with better state management"""
        buffer = np.array([], dtype=np.int16)
        max_chunk_sec = 0.5
        max_chunk_samples = int(self.sample_rate * max_chunk_sec)
        asr_buffer = b""
        silence_start_time: Optional[float] = None

        while self.is_listening:
            try:
                chunk = self.audio_queue.get(timeout=0.1)
                buffer = np.concatenate((buffer, chunk.flatten()))

                if len(buffer) >= max_chunk_samples:
                    voice_detected = self._detect_voice_activity(buffer)
                    current_time = time.time()
                    
                    if voice_detected and not self.voice_detected:
                        self.voice_detected = True
                        self.voice_start_time = current_time
                        silence_start_time = None
                        print("🎤 Voice detected...")
                        asr_buffer = b""
                    
                    elif not voice_detected and self.voice_detected:
                        if self.voice_start_time is not None:
                            self.voice_duration = current_time - self.voice_start_time
                            
                            if self.min_voice_duration <= self.voice_duration <= self.max_voice_duration:
                                print(f"🗣 Voice command detected (duration: {self.voice_duration:.1f}s)")
                                self._handle_voice_command(buffer, asr_buffer)
                            else:
                                print(f"🗣 Voice too short/long (duration: {self.voice_duration:.1f}s)")
                        
                        self.voice_detected = False
                        self.voice_start_time = None
                        silence_start_time = current_time
                    
                    elif voice_detected and self.voice_detected:
                        silence_start_time = None
                        if self.asr_enabled:
                            asr_buffer += buffer.tobytes()
                    
                    elif not voice_detected and not self.voice_detected:
                        if silence_start_time is not None:
                            silence_duration = current_time - silence_start_time
                            if silence_duration > 5.0:
                                asr_buffer = b""
                    
                    buffer = np.array([], dtype=np.int16)

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in voice detection loop: {e}")
                continue

    def _handle_voice_command(self, audio_buffer: Optional[np.ndarray] = None, asr_buffer: Optional[bytes] = None) -> None:
        """Handle detected voice command with improved error handling"""
        if self.command_callback is not None:
            try:
                command = self._recognize_speech(audio_buffer, asr_buffer)
                if command and command.strip():
                    print(f"🎯 Recognized command: {command}")
                    self.command_callback(command)
                else:
                    print("🎯 No speech recognized")
                    if self.asr_enabled:
                        self.speak("I didn't catch that. Could you repeat?")
            except Exception as e:
                self.logger.error(f"Command callback error: {e}")
                self.speak("Sorry, an error occurred while processing your command.")

    def _recognize_speech(self, audio_buffer: Optional[np.ndarray] = None, asr_buffer: Optional[bytes] = None) -> Optional[str]:
        """Recognize speech using Whisper (default) or Vosk (fallback)"""
        # Try Whisper ASR first
        if self.asr_enabled and self.whisper_asr is not None and (asr_buffer or audio_buffer is not None):
            try:
                if asr_buffer:
                    source = asr_buffer
                elif isinstance(audio_buffer, np.ndarray):
                    source = audio_buffer.tobytes()
                else:
                    source = audio_buffer
                
                if source:
                    text = self.whisper_asr.transcribe_array(source, sample_rate=self.sample_rate)
                    if text and text.strip():
                        return text.strip()
            except Exception as e:
                self.logger.error(f"Whisper recognition error: {e}")
                print("⚠️ Whisper ASR failed, trying Vosk fallback...")

        # Fallback to Vosk ASR
        if self.asr_enabled and self.vosk_recognizer is not None and asr_buffer:
            try:
                if self.vosk_recognizer.AcceptWaveform(asr_buffer):
                    result = json.loads(self.vosk_recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        return text.lower()
                
                partial = json.loads(self.vosk_recognizer.PartialResult())
                text = partial.get('partial', '').strip()
                if text:
                    return text.lower()
                    
            except Exception as e:
                self.logger.error(f"Vosk recognition error: {e}")
        
        if self.asr_enabled:
            return None
        
        # Fallback simulation if no ASR
        if audio_buffer is not None:
            rms = float(np.sqrt(np.mean(audio_buffer.astype(np.float32) ** 2)))
            normalized_rms = rms / 32768.0
            
            if normalized_rms > 0.1:
                return "hello"
            elif normalized_rms > 0.05:
                return "how are you"
            else:
                return "what time is it"
        
        return None

    def _cleanup_on_exit(self) -> None:
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
    def test_cb(cmd: str) -> None:
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
