#!/usr/bin/env python3
"""
Simple test script for the voice assistant
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import AutonomousAIAssistant

async def test_voice_assistant():
    """Test the voice assistant"""
    print("🧪 Testing Voice Assistant...")
    
    assistant = AutonomousAIAssistant()
    
    try:
        # Test TTS
        print("🔊 Testing TTS...")
        assistant.tts_manager.speak_async("Hello! This is a test of the voice assistant.")
        
        # Wait for TTS to finish
        await asyncio.sleep(3)
        
        # Load LLM model
        print("🤖 Loading LLM model...")
        if not assistant.llm_manager.load_model():
            print("❌ Failed to load LLM model")
            return
        
        # Test LLM
        print("🤖 Testing LLM...")
        test_input = "Hello, how are you?"
        response = assistant.llm_manager.generate_conversational_response(
            test_input, 
            ["notepad", "calculator", "chrome"]
        )
        
        print(f"User: {test_input}")
        print(f"Assistant: {response.get('response_text', 'No response')}")
        
        # Test TTS with LLM response
        assistant.tts_manager.speak_async(response.get('response_text', 'Test response'))
        
        await asyncio.sleep(3)
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if assistant.tts_manager:
            assistant.tts_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(test_voice_assistant())
