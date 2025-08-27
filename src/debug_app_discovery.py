#!/usr/bin/env python3
"""
Debug script to test app discovery functionality
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from controllers.system_controller import SystemController

def main():
    print("=== App Discovery Debug ===")
    
    # Initialize system controller
    controller = SystemController()
    
    # Run debug method
    controller.debug_app_discovery()
    
    # Test specific apps
    test_commands = [
        "open firefox",
        "open notepad", 
        "open calculator",
        "open word",
        "open excel",
        "firefox",
        "notepad"
    ]
    
    print("\n=== Intent Parsing Test ===")
    from core.intent_parser import AdvancedIntentParser
    parser = AdvancedIntentParser()
    
    for command in test_commands:
        result = parser.parse_command(command)
        print(f"Command: '{command}' -> {result}")

if __name__ == "__main__":
    main()
