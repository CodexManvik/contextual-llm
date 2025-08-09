"""
Enhanced Voice Interface with continuous listening and wake word detection
"""

import pyaudio
import json
import vosk
import pyttsx3
import threading
import queue
import time
import logging
from typing import Optional, Callable

class VoiceInterface:
    def __init__(self, model_path=None, wake_word="assistant"):
        import os
        if model_path is None:
            # Use absolute path to the model in your workspace
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            model_path = os.path.join(root_dir, "models", "vosk-model-en-us-0.22")
        self.model_path = model_path
        self.wake_word = wake_word.lower()
        
        # Voice recognition setup
        self.model = vosk.Model(self.model_path)
        self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
        
        # Text-to-speech setup
        self.tts_engine = pyttsx3.init()
        self._configure_tts()
        
        # Audio setup
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_wake_word_detected = False
        
        # Callback for command processing
        self.command_callback: Optional[Callable] = None
        
        # Logging
        self.logger = logging.getLogger(__name__)
    
    def _configure_tts(self):
        """Configure text-to-speech settings"""
        voices = self.tts_engine.getProperty('voices')
        if voices and isinstance(voices, (list, tuple)):
            # Try to use a female voice if available
            for voice in voices:
                if hasattr(voice, 'name') and ('female' in voice.name.lower() or 'zira' in voice.name.lower()):
                    self.tts_engine.setProperty('voice', voice.id)
                    break
        
        # Set speech rate and volume
        self.tts_engine.setProperty('rate', 180)  # Speed
        self.tts_engine.setProperty('volume', 0.8)  # Volume
    
    def speak(self, text: str):
        """Convert text to speech"""
        try:
            print(f"🔊 Assistant: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            self.logger.error(f"TTS Error: {e}")
            print(f"❌ TTS Error: {e}")
    
    def set_command_callback(self, callback: Callable):
        """Set callback function for processing commands"""
        self.command_callback = callback
    
    def start_listening(self):
        """Start continuous listening for voice commands"""
        try:
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8192,
                stream_callback=self._audio_callback
            )
            
            self.is_listening = True
            stream.start_stream()
            
            print(f"🎤 Voice interface started. Say '{self.wake_word}' to activate.")
            print("Press Ctrl+C to stop listening...")
            
            # Start processing thread
            processing_thread = threading.Thread(target=self._process_audio)
            processing_thread.daemon = True
            processing_thread.start()
            
            try:
                while self.is_listening:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping voice interface...")
            finally:
                self.is_listening = False
                stream.stop_stream()
                stream.close()
                p.terminate()
                
        except Exception as e:
            self.logger.error(f"Voice interface error: {e}")
            print(f"❌ Voice interface error: {e}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def _process_audio(self):
        """Process audio data for speech recognition"""
        partial_result = ""
        silence_counter = 0
        
        while self.is_listening:
            try:
                # Get audio data
                audio_data = self.audio_queue.get(timeout=1)
                
                if self.recognizer.AcceptWaveform(audio_data):
                    # Complete phrase recognized
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").strip()
                    
                    if text:
                        self._handle_speech_result(text)
                        silence_counter = 0
                else:
                    # Partial recognition
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get("partial", "").strip()
                    
                    if partial_text != partial_result:
                        partial_result = partial_text
                        
                        # Check for wake word in partial results
                        if not self.is_wake_word_detected and self.wake_word in partial_text.lower():
                            self._handle_wake_word()
                    
                    # Handle silence
                    if not partial_text and self.is_wake_word_detected:
                        silence_counter += 1
                        if silence_counter > 30:  # ~3 seconds of silence
                            self._reset_wake_word()
                            silence_counter = 0
                            
            except queue.Empty:
                # No audio data, continue
                continue
            except Exception as e:
                self.logger.error(f"Audio processing error: {e}")
    
    def _handle_wake_word(self):
        """Handle wake word detection"""
        if not self.is_wake_word_detected:
            self.is_wake_word_detected = True
            print(f"👂 Wake word detected! Listening for command...")
            self.speak("Yes, I'm listening.")
    
    def _reset_wake_word(self):
        """Reset wake word detection state"""
        if self.is_wake_word_detected:
            self.is_wake_word_detected = False
            print("💤 Going back to sleep mode...")
    
    def _handle_speech_result(self, text: str):
        """Handle complete speech recognition result"""
        if self.is_wake_word_detected:
            # Remove wake word from command
            command = text.lower().replace(self.wake_word, "").strip()
            
            if command:
                print(f"🎯 Command received: {command}")
                
                # Call command callback if set
                if self.command_callback:
                    try:
                        self.command_callback(command)
                    except Exception as e:
                        self.logger.error(f"Command callback error: {e}")
                        self.speak("I'm sorry, I encountered an error processing that command.")
                else:
                    self.speak("I heard your command, but I'm not connected to a command processor yet.")
                
                # Reset wake word state after processing
                self._reset_wake_word()
        elif self.wake_word in text.lower():
            # Wake word detected in complete result
            self._handle_wake_word()
    
    def stop_listening(self):
        """Stop the voice interface"""
        self.is_listening = False
        print("🛑 Voice interface stopped.")

# Test function
def test_voice_interface():
    """Test the voice interface"""
    def dummy_command_handler(command):
        print(f"Processing command: {command}")
        return f"I received the command: {command}"
    
    voice = VoiceInterface()
    voice.set_command_callback(dummy_command_handler)
    
    print("Testing Voice Interface...")
    voice.speak("Voice interface test started!")
    
    # Test listening (this will run until Ctrl+C)
    voice.start_listening()

if __name__ == "__main__":
    test_voice_interface()
