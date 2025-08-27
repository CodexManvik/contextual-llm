#!/usr/bin/env python3
"""
Test script to verify the configuration system is working correctly
"""
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.config_manager import ConfigManager

def test_config_manager():
    """Test the configuration manager functionality"""
    print("Testing Configuration Manager...")
    print("=" * 50)
    
    # Initialize config manager
    config = ConfigManager()
    
    # Test environment variables
    print("Environment Configuration:")
    print(f"NVIDIA_MODEL_PATH: {config.get_env('NVIDIA_MODEL_PATH')}")
    print(f"OLLAMA_URL: {config.get_env('OLLAMA_URL')}")
    print(f"USER_NAME: {config.get_env('USER_NAME')}")
    print(f"LOG_LEVEL: {config.get_env('LOG_LEVEL')}")
    
    # Test task type mapping
    print("\nTask Type Mapping:")
    task_mapping = config.get_task_type_mapping()
    for key, value in task_mapping.items():
        print(f"  {key}: {value}")
    
    # Test greeting templates
    print("\nGreeting Templates:")
    greeting_templates = config.get_greeting_templates()
    for key, value in greeting_templates.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for subkey, subvalue in value.items():
                print(f"    {subkey}: {subvalue}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ Configuration system test completed successfully!")

if __name__ == "__main__":
    test_config_manager()
