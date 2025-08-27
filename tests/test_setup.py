#!/usr/bin/env python3
"""
Test script to verify AI Assistant setup
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    modules = [
        ("vosk", "Vosk ASR"),
        ("pyttsx3", "pyttsx3 TTS"),
        ("faster_whisper", "Whisper ASR"),
        ("piper", "Piper TTS"),
        ("sounddevice", "Audio I/O"),
        ("numpy", "Numerical processing"),
    ]
    
    for module, description in modules:
        try:
            __import__(module)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} - not installed")
    
    print()

def test_models():
    """Test if models are available"""
    print("🎯 Testing model availability...")
    
    # Check Vosk models
    vosk_models = [
        "models/vosk/vosk-model-small-en-in-0.5"
    ]
    
    vosk_found = False
    for model in vosk_models:
        if os.path.exists(model):
            print(f"✅ Vosk model: {model}")
            vosk_found = True
            break
    
    if not vosk_found:
        print("❌ No Vosk models found")
    
    # Check Piper voices
    piper_voices = [
        "models/piper/en_GB-cori-high.onnx"
    ]
    
    piper_found = False
    for voice in piper_voices:
        if os.path.exists(voice):
            print(f"✅ Piper voice: {voice}")
            piper_found = True
            break
    
    if not piper_found:
        print("❌ No Piper voices found")
    
    # Test Whisper
    try:
        from faster_whisper import WhisperModel
        print("✅ Whisper models available (auto-download)")
    except ImportError:
        print("❌ Whisper not available")
    
    print()

def test_voice_interface():
    """Test voice interface initialization"""
    print("🎤 Testing voice interface...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        from src.interfaces.voice_interface import VoiceInterface
        
        vi = VoiceInterface()
        print("✅ Voice interface initialized successfully")
        
        # Test TTS
        vi.speak("Hello! This is a test of the voice interface.")
        print("✅ TTS test completed")
        
    except Exception as e:
        print(f"❌ Voice interface test failed: {e}")
    
    print()

def main():
    """Run all tests"""
    print("🤖 AI Assistant Setup Test")
    print("=" * 40)
    
    test_imports()
    test_models()
    test_voice_interface()
    
    print("🎉 Setup test completed!")
    print("\nIf you see any ❌ errors, run:")
    print("1. pip install -r requirements.txt")
    print("2. python download_models.py")

if __name__ == "__main__":
    main()
