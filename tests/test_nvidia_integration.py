#!/usr/bin/env python3
"""
Test script for NVIDIA Task Classifier integration
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_nvidia_classifier():
    """Test NVIDIA task classifier integration"""
    try:
        from src.models.nvidia_task_classifier import NVIDIATaskClassifier
        
        print("🧪 Testing NVIDIA Task Classifier Integration")
        print("=" * 50)
        
        # Initialize classifier
        classifier = NVIDIATaskClassifier()
        
        # Test cases
        test_commands = [
            "open firefox browser",
            "send a whatsapp message to john saying hello",
            "search for artificial intelligence on google",
            "create a new document in word",
            "what's the weather like today?",
            "play some music",
            "close all applications"
        ]
        
        print("\n🔍 Testing command classification:")
        for i, command in enumerate(test_commands, 1):
            print(f"\n{i}. Command: '{command}'")
            try:
                result = classifier.classify_prompt(command)
                print(f"   Intent: {result.get('intent', 'unknown')}")
                print(f"   Confidence: {result.get('confidence', 0):.2f}")
                print(f"   Complexity: {result.get('complexity_score', 0):.2f}")
                if 'model_used' in result:
                    print(f"   Model: {result['model_used']}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n✅ NVIDIA integration test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure NVIDIA dependencies are installed:")
        print("pip install onnxruntime-gpu")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_llm_manager_integration():
    """Test LLM Manager integration with NVIDIA classifier"""
    try:
        from src.llm_manager import ConversationalLLMManager
        
        print("\n\n🧪 Testing LLM Manager Integration")
        print("=" * 50)
        
        # Initialize LLM manager
        llm_manager = ConversationalLLMManager()
        
        # Test voice command processing
        test_command = "open firefox and search for machine learning"
        
        print(f"Testing command: '{test_command}'")
        
        # Simulate voice command processing
        result = llm_manager.process_voice_command(
            audio_data=b"",  # Empty audio for test
            recognized_text=test_command,
            confidence=0.9,
            available_apps=["firefox", "chrome", "word", "excel"]
        )
        
        print(f"Response: {result.get('response_text', 'No response')}")
        print(f"Intent: {result.get('intent', 'unknown')}")
        
        if 'intent_analysis' in result:
            intent_analysis = result['intent_analysis']
            print(f"Intent Analysis: {intent_analysis}")
        
        print("\n✅ LLM Manager integration test completed!")
        
    except Exception as e:
        print(f"❌ LLM Manager test failed: {e}")

if __name__ == "__main__":
    print("🤖 NVIDIA Integration Test Suite")
    print("=" * 50)
    
    test_nvidia_classifier()
    test_llm_manager_integration()
    
    print("\n🎉 All tests completed!")
