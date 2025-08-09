"""
Phase 2 Integration Tests
Test all components working together
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from main import AIAssistant
import time

def test_command_parsing():
    """Test command parsing functionality"""
    print("Testing Command Parsing...")
    
    assistant = AIAssistant()
    
    test_commands = [
        "send message to john saying hello world",
        "open notepad",
        "close chrome",
        "schedule meeting with sarah at 2pm tomorrow"
    ]
    
    for command in test_commands:
        print(f"\n🧪 Testing: {command}")
        parsed = assistant.command_parser.parse_command(command)
        print(f"   Result: {parsed}")

def test_system_control():
    """Test system control functionality"""
    print("\nTesting System Control...")
    
    assistant = AIAssistant()
    
    # Test opening and closing notepad
    print("📝 Testing Notepad automation...")
    
    if assistant.system_controller.open_application("notepad"):
        time.sleep(2)
        assistant.system_controller.type_text("Hello from AI Assistant Phase 2!")
        time.sleep(2)
        assistant.system_controller.close_application("notepad")
    
    print("✅ System control test completed!")

def test_voice_parsing_only():
    """Test voice interface without actual listening"""
    print("\nTesting Voice Command Processing...")
    
    assistant = AIAssistant()
    
    # Test command processing directly
    test_commands = [
        "open calculator",
        "message mom hello",
        "close notepad"
    ]
    
    for command in test_commands:
        print(f"\n🎯 Processing: {command}")
        response = assistant.process_command(command)
        print(f"   Response: {response}")

def main():
    """Run all Phase 2 tests"""
    print("🧪 PHASE 2 INTEGRATION TESTING")
    print("=" * 50)
    
    try:
        test_command_parsing()
        test_system_control()
        test_voice_parsing_only()
        
        print("\n✅ All Phase 2 tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
