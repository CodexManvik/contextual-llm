# Real-time Piper TTS Manager
import subprocess
import tempfile
import os
import threading
import queue
import wave
import pyaudio
import numpy as np
from typing import Optional
import logging

try:
    import piper
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False

class PiperTTSManager:
    def __init__(self, model_path: str = None, voice: str = "en_GB-cori-high"):
        self.logger = logging.getLogger(__name__)
        self.model_path = self._find_piper_model()
        self.voice = voice
        self.audio_queue = queue.Queue()
        self.is_speaking = False
        self.pyaudio_instance = None
        self.audio_stream = None
        self.piper_voice = None
        
        # Initialize PyAudio
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
        except Exception as e:
            self.logger.error(f"Failed to initialize PyAudio: {e}")
        
        # Initialize Piper voice
        if PIPER_AVAILABLE and self.model_path:
            try:
                self.piper_voice = piper.PiperVoice.load(self.model_path)
                self.logger.info(f"Piper voice loaded: {self.model_path}")
            except Exception as e:
                self.logger.error(f"Failed to load Piper voice: {e}")
        
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
                
                # Use command line Piper as primary method
                self._speak_with_command_line(text)
                
            except Exception as e:
                self.logger.error(f"TTS error: {e}")
            finally:
                self.is_speaking = False
        
        # Start speaking in background thread
        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()
        return True
    
    def _speak_with_piper_module(self, text: str):
        """Speak using Piper Python module"""
        try:
            # Generate audio using Piper module
            audio_data = self.piper_voice.synthesize(text)
            
            # Convert generator to bytes if needed
            if hasattr(audio_data, '__iter__') and not isinstance(audio_data, (bytes, bytearray)):
                # It's a generator, convert to bytes
                audio_chunks = []
                for chunk in audio_data:
                    self.logger.debug(f"Chunk type: {type(chunk)}, dir: {dir(chunk)}")
                    if hasattr(chunk, 'audio'):
                        # AudioChunk object - get the audio data
                        self.logger.debug(f"Audio type: {type(chunk.audio)}, dir: {dir(chunk.audio)}")
                        if hasattr(chunk.audio, 'tobytes'):
                            audio_chunks.append(chunk.audio.tobytes())
                        elif hasattr(chunk.audio, 'data'):
                            # Try to get data attribute
                            audio_chunks.append(chunk.audio.data)
                        elif hasattr(chunk.audio, 'numpy'):
                            # Try numpy method
                            audio_chunks.append(chunk.audio.numpy().tobytes())
                        else:
                            # Try to convert to bytes directly
                            try:
                                audio_chunks.append(bytes(chunk.audio))
                            except:
                                # Last resort: try to access internal data
                                audio_chunks.append(chunk.audio._data if hasattr(chunk.audio, '_data') else chunk.audio)
                    elif hasattr(chunk, 'tobytes'):
                        # Numpy array
                        audio_chunks.append(chunk.tobytes())
                    else:
                        # Direct bytes
                        audio_chunks.append(chunk)
                audio_bytes = b''.join(audio_chunks)
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            elif isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
            else:
                audio_array = audio_data
            
            # Play audio directly
            self._play_audio_array(audio_array, self.piper_voice.config.sample_rate)
            
            self.logger.info(f"Speaking: {text[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Piper module error: {e}")
            import traceback
            traceback.print_exc()
    
    def _speak_with_command_line(self, text: str):
        """Fallback to command line Piper"""
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Try to find piper executable
            piper_paths = [
                "piper",  # Try PATH first
                r"C:\Users\lenovo\AppData\Roaming\Python\Python313\Scripts\piper.exe",  # User install
                r"C:\Python313\Scripts\piper.exe",  # System install
            ]
            
            piper_cmd = None
            for path in piper_paths:
                try:
                    # Piper doesn't have --version, so just try to run it
                    result = subprocess.run([path, "--help"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0 or "usage:" in result.stderr:
                        piper_cmd = path
                        break
                except:
                    continue
            
            if not piper_cmd:
                self.logger.error("Piper executable not found")
                return
            
            # Generate speech with Piper command line
            piper_cmd = [
                piper_cmd, 
                "--model", self.model_path,
                "--output-file", temp_path
            ]
            
            process = subprocess.Popen(
                piper_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=text)
            
            if process.returncode == 0 and os.path.exists(temp_path):
                # Play audio file
                self._play_audio_file(temp_path)
                
                self.logger.info(f"Speaking: {text[:50]}...")
                
                # Clean up temporary file
                self._cleanup_temp_file(temp_path)
                
            else:
                self.logger.error(f"Piper TTS failed: {stderr}")
                
        except Exception as e:
            self.logger.error(f"Command line Piper error: {e}")
    
    def _play_audio_array(self, audio_array: np.ndarray, sample_rate: int = 22050):
        """Play audio array directly using PyAudio"""
        try:
            if not self.pyaudio_instance:
                return
                
            # Open audio stream
            self.audio_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                output=True
            )
            
            # Play audio data
            self.audio_stream.write(audio_array.tobytes())
            
            # Close stream
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
                
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")
    
    def _play_audio_file(self, file_path: str):
        """Play audio file directly using PyAudio"""
        try:
            if not self.pyaudio_instance:
                return
                
            with wave.open(file_path, 'rb') as wf:
                # Open audio stream
                self.audio_stream = self.pyaudio_instance.open(
                    format=self.pyaudio_instance.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                
                # Read and play audio data
                data = wf.readframes(1024)
                while data:
                    self.audio_stream.write(data)
                    data = wf.readframes(1024)
                
                # Close stream
                if self.audio_stream:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                    self.audio_stream = None
                    
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")
    
    def _cleanup_temp_file(self, file_path: str):
        """Clean up temporary audio file"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except:
            pass
    
    def stop_speaking(self):
        """Stop current speech"""
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            except:
                pass
    
    def cleanup(self):
        """Cleanup PyAudio resources"""
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
            self.audio_stream = None
            
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except:
                pass
            self.pyaudio_instance = None
