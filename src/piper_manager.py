# Real-time Piper TTS Manager
import subprocess
import tempfile
import os
import threading
import queue
import wave
import sys
import re
import numpy as np
from typing import Optional, Union, Generator, Any, TYPE_CHECKING
import logging

# Set encoding environment variables early
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

# Type checking imports
if TYPE_CHECKING:
    import pyaudio as PyAudioModule
    import piper
    from piper import PiperVoice as PiperVoiceClass

# Safe pyaudio import with explicit None assignment
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
    PyAudioType = pyaudio.PyAudio
    paInt16_CONSTANT = pyaudio.paInt16
except ImportError:
    pyaudio = None
    PYAUDIO_AVAILABLE = False
    PyAudioType = None
    paInt16_CONSTANT = None

# Safe piper import with explicit None assignment
try:
    import piper
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    piper = None
    PiperVoice = None
    PIPER_AVAILABLE = False

class PiperTTSManager:
    def __init__(self, model_path: Optional[str] = None, voice: str = "en_GB-cori-high"):
        self.logger = logging.getLogger(__name__)
        self.model_path = self._find_piper_model()
        self.voice = voice
        self.audio_queue: queue.Queue = queue.Queue()
        self.is_speaking = False
        self.pyaudio_instance: Optional[Any] = None
        self.audio_stream: Optional[Any] = None
        self.piper_voice: Optional[Any] = None
        
        # Store module references for safe access
        self.pyaudio_module = pyaudio if PYAUDIO_AVAILABLE else None
        self.piper_module = piper if PIPER_AVAILABLE else None
        
        # Initialize PyAudio if available
        if PYAUDIO_AVAILABLE and PyAudioType is not None:
            try:
                self.pyaudio_instance = PyAudioType()
            except Exception as e:
                self.logger.error(f"Failed to initialize PyAudio: {e}")
        
        # Initialize Piper voice if available
        if PIPER_AVAILABLE and self.model_path and PiperVoice is not None:
            try:
                self.piper_voice = PiperVoice.load(self.model_path)
                self.logger.info(f"Piper voice loaded: {self.model_path}")
            except Exception as e:
                self.logger.error(f"Failed to load Piper voice: {e}")

    def _clean_text_for_tts(self, text: str) -> str:
        """Remove or replace problematic Unicode characters for TTS"""
        # Remove emojis (Unicode ranges for common emojis)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", 
            flags=re.UNICODE
        )
        
        cleaned = emoji_pattern.sub('', text)
        
        # Encode to ASCII, ignoring problematic characters
        try:
            cleaned = cleaned.encode('ascii', errors='ignore').decode('ascii')
        except Exception:
            # Fallback: keep only basic ASCII characters
            cleaned = ''.join(char for char in cleaned if ord(char) < 128)
        
        return cleaned.strip()
        
    def _find_piper_model(self) -> str:
        """Find Piper model path"""
        possible_paths = [
            "models/piper/en_GB-cori-high.onnx",
            "./models/piper/en_GB-cori-high.onnx",
            "en_GB-cori-high.onnx"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return "en_GB-cori-high.onnx"  # Default
    
    def speak_async(self, text: str) -> bool:
        """Speak text asynchronously using Piper TTS with direct audio playback"""
        def _speak():
            try:
                self.is_speaking = True
                
                # Clean text to remove problematic Unicode characters
                cleaned_text = self._clean_text_for_tts(text)
                
                if not cleaned_text.strip():
                    self.logger.warning("No valid text to speak after cleaning")
                    return
                
                # Try Piper module first, fallback to command line
                if PIPER_AVAILABLE and self.piper_voice is not None:
                    self._speak_with_piper_module(cleaned_text)
                else:
                    self._speak_with_command_line(cleaned_text)
                
            except Exception as e:
                self.logger.error(f"TTS error: {e}")
            finally:
                self.is_speaking = False
        
        # Start speaking in background thread
        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()
        return True
    
    def _speak_with_piper_module(self, text: str):
        """Speak using Piper Python module - WAV method (most reliable)"""
        try:
            if self.piper_voice is None:
                raise RuntimeError("Piper voice not loaded")
            
            self.logger.info(f"Synthesizing with Piper WAV method: '{text}' (length: {len(text)})")
            
            # Method 1: Use Piper's built-in WAV file output (RECOMMENDED)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # This is the correct and most reliable way to use Piper TTS
                with wave.open(temp_path, 'wb') as wav_file:
                    self.piper_voice.synthesize(text, wav_file)
                
                # Check if file was created and has content
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    self.logger.info(f"Generated WAV file: {os.path.getsize(temp_path)} bytes")
                    
                    # Play the generated WAV file
                    self._play_audio_file(temp_path)
                    
                    self.logger.info(f"Successfully played: {text[:50]}...")
                else:
                    self.logger.error("No WAV file generated or file is empty")
                    raise RuntimeError("WAV generation failed")
                
            finally:
                # Clean up temporary file
                self._cleanup_temp_file(temp_path)
                
        except Exception as e:
            self.logger.error(f"Piper WAV method failed: {e}")
            # Try streaming method as fallback
            self._try_streaming_method(text)
    
    def _try_streaming_method(self, text: str):
        """Fallback streaming method for Piper"""
        try:
            if self.piper_voice is None:
                raise RuntimeError("Piper voice not loaded")
            
            self.logger.info("Trying Piper streaming method as fallback")
            
            audio_chunks = []
            
            # Try to get raw audio stream if available
            if hasattr(self.piper_voice, 'synthesize_stream_raw'):
                self.logger.debug("Using synthesize_stream_raw method")
                for audio_bytes in self.piper_voice.synthesize_stream_raw(text):
                    if isinstance(audio_bytes, (bytes, bytearray)):
                        audio_chunks.append(audio_bytes)
            else:
                # Process AudioChunk objects from regular synthesize
                self.logger.debug("Processing AudioChunk objects")
                for chunk in self.piper_voice.synthesize(text):
                    if hasattr(chunk, 'audio'):
                        # AudioChunk.audio contains the raw audio data
                        audio_data = chunk.audio
                        if hasattr(audio_data, 'tobytes'):
                            audio_chunks.append(audio_data.tobytes())
                        elif isinstance(audio_data, (bytes, bytearray)):
                            audio_chunks.append(audio_data)
                        elif hasattr(audio_data, '__array__'):
                            # Convert numpy array to bytes
                            arr = np.asarray(audio_data, dtype=np.int16)
                            audio_chunks.append(arr.tobytes())
            
            if audio_chunks:
                audio_bytes = b''.join(audio_chunks)
                if len(audio_bytes) > 0:
                    self.logger.info(f"Streaming method produced {len(audio_bytes)} bytes")
                    # Convert to numpy array and play
                    audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
                    sample_rate = getattr(self.piper_voice.config, 'sample_rate', 22050)
                    self._play_audio_array(audio_array, sample_rate)
                    self.logger.info(f"Successfully played streamed audio: {text[:50]}...")
                    return
            
            # If streaming also fails, fallback to command line
            raise RuntimeError("Streaming method failed")
            
        except Exception as e:
            self.logger.error(f"Streaming method failed: {e}")
            self.logger.info("Falling back to command line Piper")
            self._speak_with_command_line(text)
    
    def _speak_with_command_line(self, text: str):
        """Fallback to command line Piper"""
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Try to find piper executable
            piper_paths = [
                "piper",  # Try PATH first
                r"C:\Users\lenovo\AppData\Roaming\Python\Python313\Scripts\piper.exe",
                r"C:\Python313\Scripts\piper.exe",
            ]
            
            piper_cmd = None
            for path in piper_paths:
                try:
                    result = subprocess.run([path, "--help"], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=5,
                                          encoding='utf-8',
                                          errors='ignore')
                    if result.returncode == 0 or "usage:" in result.stderr:
                        piper_cmd = path
                        break
                except Exception:
                    continue
            
            if not piper_cmd:
                self.logger.error("Piper executable not found")
                return
            
            # Generate speech with Piper command line
            cmd = [
                piper_cmd, 
                "--model", self.model_path,
                "--output-file", temp_path
            ]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            stdout, stderr = process.communicate(input=text)
            
            if process.returncode == 0 and os.path.exists(temp_path):
                # Play audio file
                self._play_audio_file(temp_path)
                
                self.logger.info(f"Command line Piper success: {text[:50]}...")
                
                # Clean up temporary file
                self._cleanup_temp_file(temp_path)
                
            else:
                self.logger.error(f"Command line Piper failed: {stderr}")
                
        except Exception as e:
            self.logger.error(f"Command line Piper error: {e}")
    
    def _play_audio_array(self, audio_array: np.ndarray, sample_rate: int = 22050):
        """Play audio array directly using PyAudio"""
        try:
            if not PYAUDIO_AVAILABLE or self.pyaudio_instance is None or paInt16_CONSTANT is None:
                self.logger.warning("PyAudio not available for audio playback")
                return
                
            # Stop any existing stream
            if self.audio_stream is not None:
                try:
                    if hasattr(self.audio_stream, 'stop_stream'):
                        self.audio_stream.stop_stream()
                    if hasattr(self.audio_stream, 'close'):
                        self.audio_stream.close()
                except Exception:
                    pass
                self.audio_stream = None
                
            # Open audio stream with safe constant access
            if hasattr(self.pyaudio_instance, 'open'):
                self.audio_stream = self.pyaudio_instance.open(
                    format=paInt16_CONSTANT,
                    channels=1,
                    rate=sample_rate,
                    output=True
                )
                
                # Play audio data
                if self.audio_stream is not None and hasattr(self.audio_stream, 'write'):
                    self.audio_stream.write(audio_array.tobytes())
                
                # Close stream
                if self.audio_stream is not None:
                    if hasattr(self.audio_stream, 'stop_stream'):
                        self.audio_stream.stop_stream()
                    if hasattr(self.audio_stream, 'close'):
                        self.audio_stream.close()
                    self.audio_stream = None
                
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")
    
    def _play_audio_file(self, file_path: str):
        """Play audio file directly using PyAudio"""
        try:
            if not PYAUDIO_AVAILABLE or self.pyaudio_instance is None:
                self.logger.warning("PyAudio not available for audio playback")
                return
                
            with wave.open(file_path, 'rb') as wf:
                # Stop any existing stream
                if self.audio_stream is not None:
                    try:
                        if hasattr(self.audio_stream, 'stop_stream'):
                            self.audio_stream.stop_stream()
                        if hasattr(self.audio_stream, 'close'):
                            self.audio_stream.close()
                    except Exception:
                        pass
                    self.audio_stream = None
                
                # Open audio stream with safe method access
                if hasattr(self.pyaudio_instance, 'open') and hasattr(self.pyaudio_instance, 'get_format_from_width'):
                    self.audio_stream = self.pyaudio_instance.open(
                        format=self.pyaudio_instance.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True
                    )
                    
                    # Read and play audio data
                    if self.audio_stream is not None and hasattr(self.audio_stream, 'write'):
                        chunk_size = 1024
                        data = wf.readframes(chunk_size)
                        while data:
                            self.audio_stream.write(data)
                            data = wf.readframes(chunk_size)
                    
                    # Close stream
                    if self.audio_stream is not None:
                        if hasattr(self.audio_stream, 'stop_stream'):
                            self.audio_stream.stop_stream()
                        if hasattr(self.audio_stream, 'close'):
                            self.audio_stream.close()
                        self.audio_stream = None
                    
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")
    
    def _cleanup_temp_file(self, file_path: str):
        """Clean up temporary audio file"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass
    
    def stop_speaking(self):
        """Stop current speech"""
        if self.audio_stream is not None:
            try:
                if hasattr(self.audio_stream, 'stop_stream'):
                    self.audio_stream.stop_stream()
                if hasattr(self.audio_stream, 'close'):
                    self.audio_stream.close()
                self.audio_stream = None
            except Exception:
                pass
    
    def cleanup(self):
        """Cleanup PyAudio resources"""
        if self.audio_stream is not None:
            try:
                if hasattr(self.audio_stream, 'stop_stream'):
                    self.audio_stream.stop_stream()
                if hasattr(self.audio_stream, 'close'):
                    self.audio_stream.close()
            except Exception:
                pass
            self.audio_stream = None
            
        if self.pyaudio_instance is not None:
            try:
                if hasattr(self.pyaudio_instance, 'terminate'):
                    self.pyaudio_instance.terminate()
            except Exception:
                pass
            self.pyaudio_instance = None
