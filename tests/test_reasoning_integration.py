#!/usr/bin/env python3
"""
Test script for Reasoning Manager integration
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_reasoning_manager():
    """Test ReasoningManager functionality"""
    print("🧪 Testing Reasoning Manager Integration")
    print("=" * 50)
    
    try:
        from src.core.reasoning_manager import ReasoningManager
        
        reasoning_manager = ReasoningManager()
        
        # Test intent classification
        test_inputs = [
            "open chrome browser",
            "close firefox",
            "what's the weather today?",
            "play some music"
        ]
        
        for user_input in test_inputs:
            result = reasoning_manager.classify_intent(user_input)
            print(f"Input: '{user_input}' -> Intent: {result['intent']} (confidence: {result['confidence']:.2f})")
        
        # Test reasoning trace logging
        reasoning_manager.log_reasoning_trace("test input", {"intent": "test", "confidence": 0.9})
        print("✅ Reasoning trace logging works")
        
        # Test learning adaptation
        reasoning_manager.adapt_learning("test input", "positive feedback")
        print("✅ Learning adaptation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Reasoning Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🤖 Reasoning Manager Integration Test Suite")
    print("=" * 60)
    
    reasoning_success = test_reasoning_manager()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Reasoning Manager: {'✅ PASS' if reasoning_success else '❌ FAIL'}")
    
    if reasoning_success:
        print("\n🎉 Reasoning Manager integration is working correctly!")
        return True
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
