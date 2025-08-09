"""
AI Assistant - Phase 2 Main Application
Integrates all components for complete system control
"""

import sys
import os
import logging
import threading
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parsers.command_parser import CommandParser
from src.controllers.whatsapp_controller import WhatsAppController
from src.controllers.system_controller import SystemController
from src.interfaces.voice_interface import VoiceInterface
from typing import List, Dict, Optional, Tuple

class AIAssistant:
    def __init__(self):
        print("🤖 Initializing AI Assistant - Phase 2...")
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'assistant.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.command_parser = CommandParser()
        self.whatsapp_controller = WhatsAppController()
        self.system_controller = SystemController()
        self.voice_interface = VoiceInterface()
        
        # Set up voice command callback
        self.voice_interface.set_command_callback(self.process_command)
        
        # State tracking
        self.whatsapp_ready = False
        self.is_running = False
        
        print("✅ AI Assistant initialized successfully!")
    
    def start(self):
        """Start the AI Assistant"""
        print("\n" + "="*50)
        print("🚀 STARTING AI ASSISTANT - PHASE 2")
        print("="*50)
        
        self.is_running = True
        
        # Show startup menu
        self._show_startup_menu()
        
        # Start voice interface
        print("\n🎤 Starting voice interface...")
        self.voice_interface.speak("AI Assistant is ready!")
        
        try:
            self.voice_interface.start_listening()
        except KeyboardInterrupt:
            self.shutdown()
    
    def _show_startup_menu(self):
        """Show available features and setup options"""
        print("\n📋 Available Features:")
        print("   • Voice Commands (always active)")
        print("   • WhatsApp Web Control")
        print("   • System Automation")
        print("   • Application Management")
        print("   • File Operations")
        
        # Initialize WhatsApp if user wants
        setup_whatsapp = input("\n❓ Setup WhatsApp Web now? (y/n): ").lower() == 'y'
        if setup_whatsapp:
            if self._initialize_whatsapp():
                self.whatsapp_ready = True
                print("✅ WhatsApp Web ready!")
            else:
                print("⚠️ WhatsApp Web setup skipped. You can set it up later.")
    
    def _initialize_whatsapp(self) -> bool:
        """Initialize WhatsApp Web controller"""
        try:
            print("\n🔧 Setting up WhatsApp Web...")
            return self.whatsapp_controller.login_to_whatsapp()
        except Exception as e:
            self.logger.error(f"WhatsApp initialization failed: {e}")
            return False
    
    def process_command(self, command: str) -> str:
        """Process voice/text commands and execute actions"""
        try:
            print(f"\n🎯 Processing command: {command}")
            
            # Parse the command
            parsed_command = self.command_parser.parse_command(command)
            
            print(f"📝 Parsed: {parsed_command}")
            
            # Route to appropriate controller
            result = self._execute_command(parsed_command)
            
            # Generate response
            response = self._generate_response(parsed_command, result)
            
            # Speak response
            self.voice_interface.speak(response)
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing command: {e}"
            self.logger.error(error_msg)
            self.voice_interface.speak("I'm sorry, I encountered an error processing that command.")
            return error_msg
    
    def _execute_command(self, parsed_command: Dict) -> bool:
        """Execute the parsed command using appropriate controller"""
        intent = parsed_command.get("intent")
        action = parsed_command.get("action")
        params = parsed_command.get("parameters", {})
        try:
            if intent == "whatsapp_send":
                if not self.whatsapp_ready:
                    if not self._initialize_whatsapp():
                        return False
                    self.whatsapp_ready = True
                contact = params.get("contact")
                message = params.get("message")
                return self.whatsapp_controller.send_message(contact, message)
            elif intent == "system_control":
                app_action = params.get("action")
                application = params.get("application")
                if app_action == "open" or app_action == "launch" or app_action == "start":
                    return self.system_controller.open_application(application)
                elif app_action == "close":
                    return self.system_controller.close_application(application)
                elif app_action == "minimize":
                    return self.system_controller.minimize_application(application)
                elif app_action == "maximize":
                    return self.system_controller.maximize_application(application)
            elif intent == "calendar":
                # Calendar functionality to be implemented in Phase 3
                self.voice_interface.speak("Calendar integration coming in Phase 3!")
                return True
            elif intent == "browser":
                # Browser automation to be implemented
                website = params.get("website", params.get("query"))
                if website:
                    return self.system_controller.open_application("chrome")
                return False
            elif intent == "unknown":
                self.voice_interface.speak("I'm sorry, I didn't understand that command. Can you try rephrasing it?")
                return False
            else:
                return False
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            return False
        # Ensure a bool is always returned
        return False
    
    def _generate_response(self, parsed_command: Dict, success: bool) -> str:
        """Generate appropriate response based on command result"""
        intent = parsed_command.get("intent")
        params = parsed_command.get("parameters", {})
        
        if success:
            if intent == "whatsapp_send":
                contact = params.get("contact", "contact")
                return f"Message sent to {contact} successfully!"
            
            elif intent == "system_control":
                action = params.get("action", "action")
                app = params.get("application", "application")
                return f"Successfully {action}ed {app}!"
            
            else:
                return "Command executed successfully!"
        
        else:
            return "I'm sorry, I couldn't complete that task. Please try again or check if everything is set up correctly."
    
    def shutdown(self):
        """Shutdown the AI Assistant"""
        print("\n🛑 Shutting down AI Assistant...")
        
        self.is_running = False
        
        # Close controllers
        if self.whatsapp_controller:
            self.whatsapp_controller.close()
        
        if self.voice_interface:
            self.voice_interface.stop_listening()
        
        print("👋 AI Assistant shutdown complete!")

def main():
    """Main entry point"""
    assistant = AIAssistant()
    try:
        assistant.start()
    except KeyboardInterrupt:
        assistant.shutdown()
    except Exception as e:
        print(f"❌ Critical error: {e}")
        assistant.shutdown()

if __name__ == "__main__":
    main()
