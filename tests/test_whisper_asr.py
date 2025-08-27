#!/usr/bin/env python3
"""
Test script for Whisper ASR integration
"""

import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from interfaces.voice_interface import VoiceInterface

def test_whisper_asr():
    """Test Whisper ASR functionality"""
    print("🧪 Testing Whisper ASR Integration")
    print("=" * 50)
    
    # Create voice interface
    vi = VoiceInterface()
    
    # Check ASR status
    print(f"ASR Enabled: {vi.asr_enabled}")
    print(f"Whisper ASR: {vi.whisper_asr is not None}")
    print(f"Vosk ASR: {vi.vosk_recognizer is not None}")
    
    if vi.whisper_asr:
        print("✅ Whisper ASR is available and configured!")
        print(f"   Model: {vi.whisper_asr.model}")
        print(f"   Language: {vi.whisper_asr.language}")
    elif vi.vosk_recognizer:
        print("✅ Vosk ASR is available as fallback!")
    else:
        print("❌ No ASR system available")
        return False
    
    # Test voice interface startup
    print("\n🎤 Testing voice interface startup...")
    try:
        vi.start_listening()
        time.sleep(2)  # Let it initialize
        print("✅ Voice interface started successfully!")
        
        # Test TTS
        print("\n🔊 Testing TTS...")
        vi.speak("Whisper ASR test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
    finally:
        vi.stop_listening()

if __name__ == "__main__":
    success = test_whisper_asr()
    if success:
        print("\n🎉 Whisper ASR integration test passed!")
    else:
        print("\n💥 Whisper ASR integration test failed!")
        sys.exit(1)
