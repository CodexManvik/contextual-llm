#!/usr/bin/env python3
"""
Test script to verify the intelligent app controller integration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.context_manager import EnhancedContextManager
from core.training_data_manager import TrainingDataManager
from llm_manager import ConversationalLLMManager
from controllers.intelligent_app_controller import IntelligentAppController

def test_intelligent_controller():
    """Test the intelligent app controller functionality"""
    print("Testing Intelligent App Controller...")
    
    # Initialize required components
    llm_manager = ConversationalLLMManager()
    context_manager = EnhancedContextManager()
    training_manager = TrainingDataManager()
    
    # Initialize intelligent controller
    intelligent_controller = IntelligentAppController(
        llm_manager, 
        context_manager,
        training_manager
    )
    
    # Test basic functionality
    print("1. Testing app capability discovery...")
    capabilities = intelligent_controller.discover_app_capabilities("notepad")
    print(f"   Notepad capabilities: {len(capabilities.get('common_tasks', []))} common tasks")
    
    # Test intelligent task execution
    print("2. Testing intelligent task execution...")
    result = intelligent_controller.execute_intelligent_task(
        "notepad", 
        "open_application", 
        {"user_intent": "I want to write some notes"}
    )
    print(f"   Result: {result.get('success', False)} - {result.get('message', 'No message')}")
    
    # Test context management
    print("3. Testing context management...")
    context = context_manager.get_current_context()
    print(f"   Current context keys: {list(context.keys()) if context else 'None'}")
    
    # Test training data collection
    print("4. Testing training data...")
    stats = training_manager.get_training_stats()
    print(f"   Training stats: {stats}")
    
    # Test learned patterns
    print("5. Testing learned patterns...")
    patterns = intelligent_controller.interaction_patterns
    print(f"   Learned patterns for {len(patterns)} apps")
    
    print("✅ Intelligent App Controller test completed successfully!")

if __name__ == "__main__":
    test_intelligent_controller()
