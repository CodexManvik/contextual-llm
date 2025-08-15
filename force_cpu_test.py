#!/usr/bin/env python3
"""
Force CPU test for Whisper to bypass cuDNN errors
"""

import os
import sys

# Force CPU mode
os.environ['WHISPER_DEVICE'] = 'cpu'
os.environ['WHISPER_COMPUTE_TYPE'] = 'int8'

print("🔧 Forcing CPU mode for Whisper...")
print("WHISPER_DEVICE=cpu")
print("WHISPER_COMPUTE_TYPE=int8")

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.interfaces.voice_interface import VoiceInterface
    
    print("\n🎤 Testing Voice Interface with CPU Whisper...")
    vi = VoiceInterface()
    
    print("\n✅ Voice Interface initialized successfully!")
    print("🎯 Testing TTS...")
    vi.speak("Hello! This is a test of the voice interface with CPU Whisper.")
    
    print("\n✅ Test completed successfully!")
    print("🎉 Your AI Assistant is ready to use!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTrying to diagnose the issue...")
    
    # Test individual components
    try:
        import faster_whisper
        print("✅ faster-whisper imported successfully")
        
        # Test Whisper model loading
        model = faster_whisper.WhisperModel("small", device="cpu", compute_type="int8")
        print("✅ Whisper model loaded successfully on CPU")
        
    except Exception as e2:
        print(f"❌ Whisper test failed: {e2}")
    
    try:
        import pyttsx3
        print("✅ pyttsx3 imported successfully")
    except Exception as e3:
        print(f"❌ pyttsx3 test failed: {e3}")

print("\n" + "="*50)
print("Next steps:")
print("1. If test passed: python src/main.py")
print("2. If test failed: Check the error messages above")
print("="*50)
