# Fully Autonomous AI Assistant - Main Application
import asyncio
import logging
import threading
import time
from typing import Dict, Any, Optional
import llm_manager
import piper_manager
import controllers.system_controller
import controllers.whatsapp_controller
import interfaces.voice_interface

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
        
        # Initialize components

        self.llm_manager = llm_manager.ConversationalLLMManager()
        self.tts_manager = piper_manager.PiperTTSManager()
        self.system_controller = controllers.system_controller.AdvancedSystemController()
        self.whatsapp_controller = controllers.whatsapp_controller.WhatsAppController()
        self.voice_interface = interfaces.voice_interface.VoiceInterface()
        
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
        print("🤖 Loading LLM model...")
        if not self.llm_manager.load_model():
            print("❌ Failed to load LLM. Please check Ollama setup.")
            print("💡 Make sure Ollama is running: ollama serve")
            print("💡 And you have a model installed: ollama pull qwen2.5:7b")
            return
        
        print("✅ LLM model loaded successfully!")
        
        # Initial greeting
        greeting = "Hello! I'm your autonomous AI assistant. I can chat with you naturally, control your computer, send messages, and help with various tasks. How can I assist you today?"
        print(f"🤖 {greeting}")
        self.tts_manager.speak_async(greeting)
        
        self.is_running = True
        
        # Start continuous voice listening
        self.voice_interface.start_listening()
        
        print("\n🎤 Voice interface is active. Speak to interact with me!")
        print("💡 I'll continue listening for your commands and respond naturally.")
        print("🛑 Press Ctrl+C to stop the assistant.\n")
        
        # Keep running and handle any manual text input
        try:
            while self.is_running:
                await asyncio.sleep(0.1)  # Small delay to prevent CPU overuse
                
                # Check if voice interface is still running
                if not self.voice_interface.is_listening:
                    print("⚠️ Voice interface stopped unexpectedly. Restarting...")
                    self.voice_interface.start_listening()
                    
        except KeyboardInterrupt:
            await self.shutdown()
    
    def process_voice_input(self, user_input: str):
        """Process voice input through conversational AI"""
        if self.is_processing:
            return  # Avoid overlapping processing
        
        self.is_processing = True
        
        try:
            print(f"\n👤 User: {user_input}")
            
            # Get available apps for context
            available_apps = self.system_controller.get_all_available_apps()
            
            # Generate conversational response with intent
            response = self.llm_manager.generate_conversational_response(
                user_input, available_apps
            )
            
            response_text = response.get("response_text", "I'm not sure how to respond to that.")
            intent = response.get("intent", "conversation")
            
            print(f"🤖 Assistant: {response_text}")
            
            # Execute any system actions
            if intent != "conversation":
                # _execute_system_action is async, but process_voice_input is not
                asyncio.create_task(self._execute_system_action(response))
            
            # Speak response using the dedicated TTS manager
            self.tts_manager.speak_async(response_text)
            
        except Exception as e:
            error_response = "I encountered an error processing that. Please try again."
            print(f"❌ Error: {e}")
            self.tts_manager.speak_async(error_response)
        finally:
            self.is_processing = False
    
    async def _execute_system_action(self, response: Dict[str, Any]):
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
                    # Initialize WhatsApp if needed
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
        
        # Cleanup TTS resources
        if self.tts_manager:
            self.tts_manager.cleanup()
        
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
