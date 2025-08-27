# Real-time Piper TTS Manager - Command Line Only Version
import subprocess
import tempfile
import os
import threading
import queue
import wave
import sys
import re
import numpy as np
from typing import Optional, Any, TYPE_CHECKING
import logging

# Set encoding environment variables early
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

# Type checking imports
if TYPE_CHECKING:
    import pyaudio as PyAudioModule

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

class PiperTTSManager:
    def __init__(self, model_path: Optional[str] = None, voice: str = "en_GB-cori-high"):
        self.logger = logging.getLogger(__name__)
        self.model_path = self._find_piper_model()
        self.voice = voice
        self.audio_queue: queue.Queue = queue.Queue()
        self.is_speaking = False
        self.pyaudio_instance: Optional[Any] = None
        self.audio_stream: Optional[Any] = None
        
        # Store module references for safe access
        self.pyaudio_module = pyaudio if PYAUDIO_AVAILABLE else None
        
        # Initialize PyAudio if available
        if PYAUDIO_AVAILABLE and PyAudioType is not None:
            try:
                self.pyaudio_instance = PyAudioType()
            except Exception as e:
                self.logger.error(f"Failed to initialize PyAudio: {e}")

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
            "../models/piper/en_GB-cori-high.onnx",  # From src directory
            "models/piper/en_GB-cori-high.onnx",     # From project root
            "./models/piper/en_GB-cori-high.onnx",   # From project root
            "piper/en_GB-cori-high.onnx",            # Relative to current dir
            "en_GB-cori-high.onnx"                   # Default
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Found Piper model at: {os.path.abspath(path)}")
                return path
        
        print("Warning: Piper model not found in any of the expected locations")
        return "en_GB-cori-high.onnx"  # Default
    
    def speak_async(self, text: str) -> bool:
        """Speak text asynchronously using command line Piper TTS"""
        def _speak():
            try:
                self.is_speaking = True
                
                # Clean text to remove problematic Unicode characters
                cleaned_text = self._clean_text_for_tts(text)
                
                if not cleaned_text.strip():
                    self.logger.warning("No valid text to speak after cleaning")
                    return
                
                # Use command line Piper (only method)
                self._speak_with_command_line(cleaned_text)
                
            except Exception as e:
                self.logger.error(f"TTS error: {e}")
            finally:
                self.is_speaking = False
        
        # Start speaking in background thread
        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()
        return True
    
    def _speak_with_command_line(self, text: str):
        """Use command line Piper for TTS"""
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
            # Use the absolute path to ensure command line Piper can find the model
            absolute_model_path = os.path.abspath(self.model_path)
            cmd = [
                piper_cmd, 
                "--model", absolute_model_path,
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
