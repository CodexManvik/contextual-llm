"""
AI Assistant - Phase 2 Main Application
Integrates all components for complete system control
"""

import sys
import os
import logging
import threading
import time

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, continue without .env support

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
        
        # Ensure logs folder exists before logging setup
        os.makedirs('logs', exist_ok=True)
        
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
        
        # Preload a sample list to confirm discovery is working
        sample = self.system_controller.list_discovered_apps(limit=10)
        self.logger.info(f"Discovered apps sample: {sample}")
        
        # Set up voice command callback
        def command_callback(command: str) -> None:
            self.process_command(command)
        self.voice_interface.set_command_callback(command_callback)
        
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
        self.voice_interface.speak("AI Assistant is ready! Voice detection mode active.")
        
        try:
            self.voice_interface.start_listening()
            
            # Keep the main thread alive
            print("\n🔄 AI Assistant is running...")
            print("💡 Try speaking to trigger voice detection!")
            print("📝 You can also type commands directly in the terminal.")
            
            # Main loop to keep the application running
            while self.is_running:
                try:
                    # Check for direct input commands
                    user_input = input("\n🎯 Enter command (or press Enter to continue): ").strip()
                    if user_input:
                        self.process_command(user_input)
                except (EOFError, KeyboardInterrupt):
                    break
                except Exception as e:
                    self.logger.error(f"Input error: {e}")
                    break
                    
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.logger.error(f"Voice interface error: {e}")
            print(f"❌ Voice interface error: {e}")
            self.shutdown()
    
    def _show_startup_menu(self):
        """Show available features and setup options"""
        print("\n📋 Available Features:")
        print("   • Voice Commands (always active)")
        print("   • WhatsApp Web Control")
        print("   • System Automation")
        print("   • Application Management")
        print("   • File Operations")
        
        # Initialize WhatsApp if user wants (skip prompt in non-interactive environments)
        try:
            is_interactive = sys.stdin is not None and sys.stdin.isatty()
        except Exception:
            is_interactive = False

        if is_interactive:
            setup_whatsapp = input("\n❓ Setup WhatsApp Web now? (y/n): ").lower() == 'y'
        else:
            print("\nℹ️ Non-interactive environment detected. Skipping WhatsApp setup prompt.")
            setup_whatsapp = False
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
            
            # Check for quick utility commands before normal parsing
            cmd_lower = (command or "").strip().lower()
            if cmd_lower in ("list applications","list apps","show applications","show apps"):
                names = self.system_controller.list_discovered_apps(limit=25)
                msg = "Top discovered apps: " + ", ".join(names) if names else "No applications discovered."
                self.voice_interface.speak(msg)
                return msg

            if cmd_lower in ("refresh applications","rescan applications","rescan apps","refresh apps"):
                count = self.system_controller.refresh_app_registry()
                msg = f"Rescanned applications. Found {count} entries."
                self.voice_interface.speak(msg)
                return msg
            
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
                app_action = params.get("action") or parsed_command.get("action")
                application = params.get("application")

                if app_action in ("list_apps",):
                    names = self.system_controller.list_discovered_apps(limit=25)
                    self.voice_interface.speak("Top applications: " + ", ".join(names) if names else "No applications found.")
                    return True

                if app_action in ("refresh_apps",):
                    count = self.system_controller.refresh_app_registry()
                    self.voice_interface.speak(f"Rescanned and found {count} applications.")
                    return True

                if app_action in ("open","launch","start"):
                    if self.system_controller.open_discovered_app(application):
                        return True
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
