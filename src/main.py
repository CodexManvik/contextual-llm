from dotenv import load_dotenv
load_dotenv()

import warnings
warnings.filterwarnings('ignore', message='pkg_resources is deprecated')

import os, sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

# Set console code page to UTF-8 for Windows
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
    except:
        pass

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Your existing imports (assuming these exist in your structure)
from controllers.whatsapp_controller import WhatsAppController
from controllers.system_controller import SystemController  # Use enhanced version
from interfaces.voice_interface import VoiceInterface

# New imports for enhanced features
from llm_manager import ConversationalLLMManager
from piper_manager import PiperTTSManager
from memory.memory_manager import ContextualMemoryManager
from memory.context_manager import AdvancedContextManager
from retrieval.rag_manager import RetrievalAugmentedGeneration
from planning.task_planner import ProactivePlanner

# Context and Training managers for Intelligent Controller
from core.context_manager import EnhancedContextManager
from core.training_data_manager import TrainingDataManager

# Intelligent App Controller import
from controllers.intelligent_app_controller import IntelligentAppController

# Configuration Manager
from config.config_manager import ConfigManager

# Reasoning System
from core.reasoning_manager import ReasoningManager
# Monitoring System
from core.monitoring import MonitoringManager
# Enhanced Logging System
from core.logging_utils import setup_global_logging, get_logger

class AutonomousAIAssistant:
    def __init__(self):
        print("Initializing Autonomous AI Assistant...")
        
        import tempfile
        
        # Create a temporary directory for logs
        self.temp_log_dir = tempfile.TemporaryDirectory()
        log_file_path = os.path.join(self.temp_log_dir.name, 'autonomous_assistant.log')
        
        # Setup logging from environment variables
        log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        
        # Initialize monitoring manager
        self.monitoring_manager = MonitoringManager(self.config_manager)
        
        # Initialize reasoning manager
        self.reasoning_manager = ReasoningManager()
        
        # Initialize core components
        self.llm_manager = ConversationalLLMManager()
        self.tts_manager = PiperTTSManager()
        self.system_controller = SystemController()
        self.whatsapp_controller = WhatsAppController()
        self.voice_interface = VoiceInterface()
        
        # Initialize context and training managers for intelligent controller
        self.enhanced_context_manager = EnhancedContextManager()
        self.training_data_manager = TrainingDataManager()
        
        # Initialize Intelligent App Controller with required managers
        self.intelligent_controller = IntelligentAppController(
            self.llm_manager, 
            self.enhanced_context_manager,
            self.training_data_manager
        )
        
        # Inject intelligent controller into system controller
        self.system_controller.set_intelligent_controller(self.intelligent_controller)
        
        # New Enhanced managers
        self.memory_manager = ContextualMemoryManager()
        self.context_manager = AdvancedContextManager()
        self.rag_manager = RetrievalAugmentedGeneration()
        self.task_planner = ProactivePlanner(self.llm_manager)
        
        # State
        self.is_running = False
        self.is_processing = False
        self.whatsapp_ready = False
        
        # Setup voice callback
        self.voice_interface.set_command_callback(self.process_voice_input)
        print("Autonomous AI Assistant initialized!")
    
    def _get_dynamic_greeting(self) -> str:
        """Generate a dynamic greeting based on time of day and user preferences"""
        try:
            current_hour = datetime.now().hour
            user_name = self.config_manager.get_env('USER_NAME', 'User')
            greeting_style = self.config_manager.get_env('GREETING_STYLE', 'friendly')
            templates = self.config_manager.get_greeting_templates()
            
            # Determine time of day
            if 5 <= current_hour < 12:
                time_of_day = "morning"
            elif 12 <= current_hour < 17:
                time_of_day = "afternoon"
            elif 17 <= current_hour < 21:
                time_of_day = "evening"
            else:
                time_of_day = "default"
            
            # Get personalized greeting based on style
            personalized_templates = templates.get('personalized', {})
            if greeting_style in personalized_templates:
                greeting = personalized_templates[greeting_style].format(
                    name=user_name,
                    time_of_day=time_of_day
                )
            else:
                # Fallback to time-based greeting
                greeting = templates.get(time_of_day, templates.get('default', 
                    "Hello! I'm your AI assistant. How can I help you today?"))
            
            return greeting
            
        except Exception as e:
            self.logger.error(f"Error generating dynamic greeting: {e}")
            return "Hello! I'm your AI assistant. How can I help you today?"
    
    async def start(self):
        """Start the autonomous assistant"""
        print("=" * 60)
        print("STARTING AUTONOMOUS AI ASSISTANT")
        print("=" * 60)
        
        # Load LLM with enhanced error handling
        try:
            if not self.llm_manager.load_model():
                print("Failed to load LLM. Please check Ollama setup.")
                return
        except Exception as e:
            self.logger.error(f"Error loading LLM: {e}")
            print(f"Critical error loading LLM: {e}")
            return
        
        # Generate dynamic greeting
        greeting = self._get_dynamic_greeting()
        print(f"> {greeting}")
        self.tts_manager.speak_async(greeting)
        self.is_running = True
        
        # Start monitoring system
        self.monitoring_manager.start_all_monitoring()
        
        # Start continuous voice listening
        self.voice_interface.start_listening()
        
        try:
            # Keep running and handle any manual text input
            while self.is_running:
                await asyncio.sleep(0.1)  # Small delay to prevent CPU overuse
        except KeyboardInterrupt:
            await self.shutdown()
    
    def process_voice_input(self, user_input: str):
        """Process voice input through enhanced AI"""
        if self.is_processing:
            return
        
        self.is_processing = True
        start_time = time.time()
        
        # Update monitoring state
        self.monitoring_manager.update_processing_state(True)
        
        try:
            print(f"> User: {user_input}")
            
            # Get available apps for context
            available_apps = self.system_controller.get_all_available_apps()
            
            # Process with enhanced AI (THIS IS THE MAIN CHANGE)
            response = self.llm_manager.process_voice_command(
                audio_data=b"",  # You'd get this from your voice interface
                recognized_text=user_input,
                confidence=0.8,  # You'd get this from Whisper
                available_apps=available_apps
            )
            
            response_text = response.get("response_text", "I'm not sure how to respond.")
            intent_analysis = response.get("intent_analysis", {})
            
            print(f"> Assistant: {response_text}")
            
            # Execute system actions using AI analysis
            if intent_analysis.get("intent") != "conversation":
                self.execute_system_action(response)
            
            # Speak response
            self.tts_manager.speak_async(response_text)
            
            # Show AI stats occasionally
            if len(self.llm_manager.conversation_history) % 10 == 0:
                stats = self.llm_manager.get_ai_stats()
                print(f"> AI Stats: {stats}")
                
            # Record processing time for monitoring
            processing_time = time.time() - start_time
            self.monitoring_manager.record_command(processing_time)
            
            # Add learning data for background adaptation
            learning_data = {
                'user_input': user_input,
                'response': response_text,
                'intent': intent_analysis.get('intent', 'unknown'),
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat()
            }
            self.monitoring_manager.add_learning_data(learning_data)
                
        except Exception as e:
            # Record error in monitoring
            self.monitoring_manager.record_error()
            
            # Learn from errors
            self.llm_manager.learn_from_correction(user_input, f"system error: {e}")
            error_response = "I encountered an error. Let me learn from this."
            print(f"> Error: {e}")
            self.tts_manager.speak_async(error_response)
        finally:
            self.is_processing = False
            self.monitoring_manager.update_processing_state(False)
    
    def execute_system_action(self, response: Dict[str, Any]):
        """Execute system actions based on LLM response with intelligent execution"""
        intent = response.get("intent")
        action = response.get("action")
        parameters = response.get("parameters", {})
        intent_analysis = response.get("intent_analysis", {})

        try:
            # Check if this is a complex task that requires intelligent execution
            if self._should_use_intelligent_execution(intent, action, parameters, intent_analysis):
                self._execute_intelligent_task(intent, action, parameters, intent_analysis)
            else:
                # Use basic execution for simple commands
                self._execute_basic_action(intent, action, parameters)
                
        except Exception as e:
            self.logger.error(f"Action execution error: {e}")
            # Try to learn from the error
            self._handle_execution_error(e, intent, action, parameters)
    
    def _should_use_intelligent_execution(self, intent: Optional[str], action: Optional[str], parameters: Dict[str, Any], intent_analysis: Dict[str, Any]) -> bool:
        """Determine if intelligent execution should be used based on intent and action."""
        # Handle None values
        if intent is None or action is None:
            return False
        
        # Logic to determine if intelligent execution is appropriate
        return intent in ["system_control", "whatsapp_send"] and action in ["open", "launch", "send"]

    def _execute_intelligent_task(self, intent: Optional[str], action: Optional[str], parameters: Dict[str, Any], intent_analysis: Dict[str, Any]):
        """Execute a task using the intelligent controller."""
        app_name = parameters.get("application", "")
        user_intent = intent_analysis.get("intent", "")
        context = self.enhanced_context_manager.get_current_context()
        
        result = self.intelligent_controller.execute_intelligent_task(app_name, user_intent, context)
        print(result.get("message", "Task execution initiated."))

    def _execute_basic_action(self, intent: Optional[str], action: Optional[str], parameters: Dict[str, Any]):
        """Execute basic actions based on intent and action."""
        if intent == "system_control":
            if action in ["open", "launch", "start"]:
                app_name = parameters.get("application", "")
                result = self.system_controller.open_any_application(app_name)
                if result["success"]:
                    print(result["message"])
            elif action == "close":
                app_name = parameters.get("application", "")
                if app_name:
                    result = self.system_controller.close_application(app_name)
                    if result["success"]:
                        print(result["message"])
                    else:
                        print(f"Failed to close {app_name}: {result['message']}")
                else:
                    print("No application specified to close")

    def _handle_execution_error(self, error: Exception, intent: Optional[str], action: Optional[str], parameters: Dict[str, Any]):
        """Handle errors that occur during action execution."""
        intent_str = str(intent) if intent is not None else "unknown"
        action_str = str(action) if action is not None else "unknown"
        self.logger.error(f"Error executing {intent_str} with action {action_str}: {error}")
        # Additional error handling logic can be added here

    async def shutdown(self):
        """Shutdown the assistant"""
        print("Shutting down Autonomous AI Assistant...")
        self.is_running = False
        
        # Cleanup
        if self.voice_interface:
            self.voice_interface.stop_listening()
        if self.whatsapp_controller:
            self.whatsapp_controller.close()
        
        # Clean up temporary log directory
        if hasattr(self, 'temp_log_dir'):
            self.temp_log_dir.cleanup()
        
        # Final goodbye
        goodbye = "Goodbye! I'm shutting down now."
        print(f"> {goodbye}")
        self.tts_manager.speak_async(goodbye)
        
        # Wait a moment for TTS to finish
        time.sleep(2)
        print("Shutdown complete!")

# Main entry point
async def main():
    assistant = AutonomousAIAssistant()
    try:
        await assistant.start()
    except KeyboardInterrupt:
        await assistant.shutdown()
    except Exception as e:
        print(f"Critical error: {e}")
        await assistant.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
