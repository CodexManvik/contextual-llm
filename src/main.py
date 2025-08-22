# Fully Autonomous AI Assistant - Main Application
from dotenv import load_dotenv
load_dotenv()
import os,sys

os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

if sys.platform == 'win32':
    try:
        # Set console code page to UTF-8
        os.system('chcp 65001 >nul 2>&1')
    except:
        pass

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Your existing imports (assuming these exist in your structure)
from parsers.command_parser import CommandParser
from controllers.whatsapp_controller import WhatsAppController
from controllers.system_controller import AdvancedSystemController  # Use enhanced version
from interfaces.voice_interface import VoiceInterface

# New imports for enhanced features
from llm_manager import ConversationalLLMManager
from piper_manager import PiperTTSManager
from memory.memory_manager import ContextualMemoryManager
from memory.context_manager import AdvancedContextManager
from retrieval.rag_manager import RetrievalAugmentedGeneration
from planning.task_planner import ProactivePlanner

class AutonomousAIAssistant:
    def __init__(self):
        print("🤖 Initializing Autonomous AI Assistant...")
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/autonomous_assistant.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.llm_manager = ConversationalLLMManager()
        self.tts_manager = PiperTTSManager()
        self.system_controller = AdvancedSystemController()
        self.whatsapp_controller = WhatsAppController()
        self.voice_interface = VoiceInterface()
        
        # New: Enhanced managers
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
        
        print("✅ Autonomous AI Assistant initialized!")
    
    async def start(self):
        """Start the autonomous assistant"""
        print("\n" + "="*60)
        print("🚀 STARTING AUTONOMOUS AI ASSISTANT")
        print("="*60)
        
        # Load LLM
        if not self.llm_manager.load_model():
            print("❌ Failed to load LLM. Please check Ollama setup.")
            return
        
        # Initial greeting
        greeting = "Hello! I'm your autonomous AI assistant. I can chat with you naturally, control your computer, send messages, and help with various tasks. How can I assist you today?"
        print(f"🤖 {greeting}")
        self.tts_manager.speak_async(greeting)
        
        self.is_running = True
        
        # Start continuous voice listening
        self.voice_interface.start_listening()
        
        # Keep running and handle any manual text input
        try:
            while self.is_running:
                await asyncio.sleep(0.1)  # Small delay to prevent CPU overuse
        except KeyboardInterrupt:
            await self.shutdown()
    
    # Update your process_voice_input method:
    def process_voice_input(self, user_input: str):
        """Process voice input through enhanced AI"""
        if self.is_processing:
            return
        
        self.is_processing = True
        
        try:
            print(f"\n👤 User: {user_input}")
            
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
            
            print(f"🤖 Assistant: {response_text}")
            
            # Execute system actions using AI analysis
            if intent_analysis.get("intent") != "conversation":
                self._execute_system_action(response)
            
            # Speak response
            self.tts_manager.speak_async(response_text)
            
            # Show AI stats occasionally
            if len(self.llm_manager.conversation_history) % 10 == 0:
                stats = self.llm_manager.get_ai_stats()
                print(f"🧠 AI Stats: {stats}")
            
        except Exception as e:
            # Learn from errors
            self.llm_manager.learn_from_correction(user_input, "system error")
            error_response = "I encountered an error. Let me learn from this."
            print(f"❌ Error: {e}")
            self.tts_manager.speak_async(error_response)
        finally:
            self.is_processing = False

    
    def _execute_system_action(self, response: Dict[str, Any]):
        """Execute system actions based on LLM response"""
        intent = response.get("intent")
        action = response.get("action")
        parameters = response.get("parameters", {})
        
        try:
            if intent == "system_control":
                if action in ["open", "launch", "start"]:
                    app_name = parameters.get("application", "")
                    result = self.system_controller.open_any_application(app_name)
                    if result["success"]:
                        print(f"✅ {result['message']}")
                
                elif action == "close":
                    # Implementation for closing apps
                    pass
            
            elif intent == "whatsapp_send":
                if not self.whatsapp_ready:
                    self.whatsapp_ready = self.whatsapp_controller.login_to_whatsapp()
                
                if self.whatsapp_ready:
                    contact = parameters.get("contact", "")
                    message = parameters.get("message", "")
                    if contact and message:
                        success = self.whatsapp_controller.send_message(contact, message)
                        if success:
                            print(f"✅ WhatsApp message sent to {contact}")
            
            elif intent == "web_search":
                query = parameters.get("query", "")
                if query:
                    self.system_controller.web_search(query)
                    print(f"✅ Web search performed: {query}")
            
            elif intent == "keyboard_mouse":
                action_type = parameters.get("action_type", "")
                if action_type == "type":
                    text = parameters.get("text", "")
                    self.system_controller.keyboard_action("type", text=text)
                elif action_type == "click":
                    self.system_controller.mouse_action("click")
            
            elif intent == "file_operation":
                operation = parameters.get("operation", "")
                result = self.system_controller.file_operation(operation, **parameters)
                print(f"📁 File operation: {result['message']}")
                
        except Exception as e:
            self.logger.error(f"Action execution error: {e}")
    
    async def shutdown(self):
        """Shutdown the assistant"""
        print("\n🛑 Shutting down Autonomous AI Assistant...")
        
        self.is_running = False
        
        # Cleanup
        if self.voice_interface:
            self.voice_interface.stop_listening()
        
        if self.whatsapp_controller:
            self.whatsapp_controller.close()
        
        # Final goodbye
        goodbye = "Goodbye! I'm shutting down now."
        print(f"🤖 {goodbye}")
        self.tts_manager.speak_async(goodbye)
        
        # Wait a moment for TTS to finish
        time.sleep(2)
        
        print("👋 Shutdown complete!")

# Main entry point
async def main():
    assistant = AutonomousAIAssistant()
    try:
        await assistant.start()
    except KeyboardInterrupt:
        await assistant.shutdown()
    except Exception as e:
        print(f"❌ Critical error: {e}")
        await assistant.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
