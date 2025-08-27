#!/usr/bin/env python3
"""
Complete system test to verify intent parsing and app execution
"""

import sys
import os
import logging
import asyncio

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from core.intent_parser import AdvancedIntentParser
from controllers.system_controller import SystemController

def test_intent_parsing():
    """Test intent parsing with various commands"""
    print("=== INTENT PARSING TESTS ===")
    
    parser = AdvancedIntentParser()
    
    test_cases = [
        # Valid app opening commands
        ("open firefox", "system_control"),
        ("launch notepad", "system_control"),
        ("start calculator", "system_control"),
        ("firefox", "system_control"),
        ("notepad", "system_control"),
        ("calculator", "system_control"),
        
        # Conversation commands
        ("hello", "conversation"),
        ("hi there", "conversation"),
        ("how are you", "conversation"),
        ("thank you", "conversation"),
        
        # Unknown commands
        ("random text", "unknown"),
        ("what is this", "unknown"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for command, expected_intent in test_cases:
        result = parser.parse_command(command)
        actual_intent = result.get("intent", "unknown")
        
        if actual_intent == expected_intent:
            print(f"✓ PASS: '{command}' -> {actual_intent} (confidence: {result.get('confidence', 0)})")
            passed += 1
        else:
            print(f"✗ FAIL: '{command}' -> expected {expected_intent}, got {actual_intent}")
    
    print(f"\nIntent Parsing Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    return passed == total

def test_app_execution():
    """Test app execution with mock system controller"""
    print("\n=== APP EXECUTION TESTS ===")
    
    controller = SystemController()
    
    # Test apps that should work
    test_apps = [
        ("notepad", True),  # Should work
        ("firefox", True),  # Should work
        ("calculator", True),  # Should work
        ("nonexistent_app", False),  # Should fail
    ]
    
    passed = 0
    total = len(test_apps)
    
    for app_name, should_succeed in test_apps:
        try:
            result = controller.open_any_application(app_name)
            success = result.get("success", False)
            
            if success == should_succeed:
                print(f"✓ PASS: '{app_name}' -> {'Success' if success else 'Failed'} (expected: {'Success' if should_succeed else 'Failed'})")
                passed += 1
            else:
                print(f"✗ FAIL: '{app_name}' -> {'Success' if success else 'Failed'} (expected: {'Success' if should_succeed else 'Failed'})")
                if "message" in result:
                    print(f"    Message: {result['message']}")
                    
        except Exception as e:
            print(f"✗ ERROR: '{app_name}' -> Exception: {e}")
    
    print(f"\nApp Execution Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    return passed == total

def test_error_handling():
    """Test error handling and edge cases"""
    print("\n=== ERROR HANDLING TESTS ===")
    
    parser = AdvancedIntentParser()
    
    # Test edge cases
    edge_cases = [
        "",  # Empty string
        "   ",  # Whitespace only
        "open",  # Just "open" without app name
        "close",  # Just "close" without app name
    ]
    
    passed = 0
    total = len(edge_cases)
    
    for command in edge_cases:
        try:
            result = parser.parse_command(command)
            # Should not crash and should return unknown intent or handle gracefully
            if "intent" in result:
                print(f"✓ PASS: '{command}' -> handled gracefully: {result['intent']}")
                passed += 1
            else:
                print(f"✗ FAIL: '{command}' -> no intent in result")
        except Exception as e:
            print(f"✗ ERROR: '{command}' -> Exception: {e}")
    
    print(f"\nError Handling Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    return passed == total

def main():
    """Run all tests"""
    print("=== COMPLETE SYSTEM TEST ===")
    
    # Run all tests
    intent_passed = test_intent_parsing()
    execution_passed = test_app_execution()
    error_passed = test_error_handling()
    
    print("\n=== FINAL RESULTS ===")
    print(f"Intent Parsing: {'PASS' if intent_passed else 'FAIL'}")
    print(f"App Execution: {'PASS' if execution_passed else 'FAIL'}")
    print(f"Error Handling: {'PASS' if error_passed else 'FAIL'}")
    
    overall_pass = intent_passed and execution_passed and error_passed
    print(f"\nOverall Result: {'ALL TESTS PASSED! ✅' if overall_pass else 'SOME TESTS FAILED! ❌'}")
    
    if overall_pass:
        print("\n🎉 The intent parser fixes have successfully resolved the tuple index errors!")
        print("The system is now stable and ready for use.")
    else:
        print("\n⚠️  Some issues remain that need to be addressed.")

if __name__ == "__main__":
    main()
