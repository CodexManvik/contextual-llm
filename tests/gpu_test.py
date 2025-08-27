#!/usr/bin/env python3
"""
GPU Test for Whisper to ensure it runs on CUDA
"""

import os
import sys

# Set environment variables for GPU testing
os.environ['WHISPER_DEVICE'] = 'cuda'
os.environ['WHISPER_COMPUTE_TYPE'] = 'int8_float16'

print("🔧 Testing GPU mode for Whisper...")
print("WHISPER_DEVICE=cuda")
print("WHISPER_COMPUTE_TYPE=int8_float16")

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.interfaces.voice_interface import VoiceInterface
    
    print("\n🎤 Testing Voice Interface with GPU Whisper...")
    vi = VoiceInterface()
    
    print("\n✅ Voice Interface initialized successfully!")
    print("🎯 Testing TTS...")
    vi.speak("Hello! This is a test of the voice interface with GPU Whisper.")
    
    print("\n✅ Test completed successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTrying to diagnose the issue...")
    
    # Test individual components
    try:
        import faster_whisper
        print("✅ faster-whisper imported successfully")
        
        # Test Whisper model loading
        model = faster_whisper.WhisperModel("small", device="cuda", compute_type="int8_float16")
        print("✅ Whisper model loaded successfully on GPU")
        
    except Exception as e2:
        print(f"❌ Whisper test failed: {e2}")

print("\n" + "="*50)
print("Next steps:")
print("1. If test passed: python src/main.py")
print("2. If test failed: Check the error messages above")
print("="*50)
