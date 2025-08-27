import pyaudio
import json
import vosk
import sys
import os

# Check if model exists
model_path = "vosk-model-en-in-0.5"
if not os.path.exists(model_path):
    print(f"Model not found at {model_path}")
    print("Download from: https://alphacephei.com/vosk/models")
    sys.exit(1)

# Initialize Vosk
model = vosk.Model(model_path)
recognizer = vosk.KaldiRecognizer(model, 16000)

# Initialize PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8192)

print("Listening... (Press Ctrl+C to stop)")
print("Say something to test voice recognition!")

try:
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            if result["text"]:
                print(f"You said: {result['text']}")
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
