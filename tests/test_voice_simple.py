#!/usr/bin/env python3
"""
Simple test script for voice interface without NeMo
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.interfaces.voice_interface import VoiceInterface
import time

def test_voice_interface():
    """Test voice interface with voice detection"""
    print("🧪 Testing Voice Interface (Voice Detection Mode)")
    print("=" * 40)
    
    try:
        # Create voice interface
        vi = VoiceInterface()
        
        # Test TTS
        print("🔊 Testing Text-to-Speech...")
        vi.speak("Hello! This is a test of the voice interface.")
        time.sleep(1)
        
        # Test voice detection
        print("🎤 Testing voice detection...")
        vi.start_listening()
        
        # Let it run for a few seconds
        print("⏱️ Running for 10 seconds...")
        print("🔊 Speak to trigger voice detection events...")
        time.sleep(10)
        
        # Stop
        vi.stop_listening()
        
        print("✅ Voice interface test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_voice_interface()
    sys.exit(0 if success else 1)
