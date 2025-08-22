# Enhanced LLM Manager with Context & Conversation
import os
import logging
import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque

# Import all AI components
from core.intent_parser import AdvancedIntentParser
from core.context_manager import EnhancedContextManager
from core.voice_optimizer import VoiceRecognitionOptimizer

class ConversationalLLMManager:
    def __init__(self, model_name: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "gemma2:2b")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.is_loaded = False
        
        # Initialize AI components
        self.intent_parser = AdvancedIntentParser()
        self.enhanced_context = EnhancedContextManager()
        self.voice_optimizer = VoiceRecognitionOptimizer()
        
        # Legacy conversation context (for compatibility)
        self.conversation_history: List[Dict[str, str]] = []
        self.system_context = {
            "user_name": "User",
            "assistant_name": "AI Assistant",
            "capabilities": [
                "open/close applications", "send WhatsApp messages", "control mouse/keyboard",
                "web searches", "file operations", "casual conversation", "system automation"
            ]
        }
    
    def load_model(self) -> bool:
        """Load and test Ollama model"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False
            
            models = response.json().get("models", [])
            available_models = [model["name"] for model in models]
            
            if not any(self.model_name in m for m in available_models):
                if available_models:
                    self.model_name = available_models[0]
            
            self.is_loaded = True
            self.logger.info(f"Using model: {self.model_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False
    
    def add_to_context(self, role: str, content: str):
        """Add message to conversation context (legacy compatibility)"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep context manageable (last 20 messages)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def process_voice_command(self, audio_data: bytes, recognized_text: str, 
                             confidence: float, available_apps: Optional[List[str]] = None) -> Dict[str, Any]:
        """Enhanced voice command processing with learning - MAIN ENTRY POINT"""
        if available_apps is None:
            available_apps = []
            
        try:
            # Step 1: Optimize voice recognition
            voice_result = self.voice_optimizer.process_recognition_result(
                audio_data, recognized_text, confidence
            )
            
            # Use improved text
            improved_text = voice_result["improved_text"]
            self.logger.info(f"Voice optimization: '{recognized_text}' -> '{improved_text}'")
            
            # Step 2: Get enhanced context
            current_context = self.enhanced_context.get_current_context()
            
            # Add available apps to context
            if available_apps:
                current_context["available_apps"] = available_apps
            
            # Step 3: Parse intent with advanced parser
            intent_analysis = self.intent_parser.parse_command(improved_text, current_context)
            self.logger.info(f"Intent analysis: {intent_analysis}")
            
            # Step 4: Generate conversational response
            response = self.generate_conversational_response(improved_text, current_context)
            
            # Step 5: Enhance response with AI analysis
            response["voice_optimization"] = voice_result
            response["intent_analysis"] = intent_analysis
            response["ai_recommendations"] = self.enhanced_context.get_recommendations()
            
            # Step 6: Learn from this interaction
            self._learn_from_interaction(improved_text, response, intent_analysis)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in voice command processing: {e}")
            return self._generate_error_response(recognized_text)
    
    def generate_conversational_response(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate both conversation response and action intent"""
        
        # Extract available_apps from context (fallback to empty list)
        available_apps = context.get("available_apps", []) if isinstance(context.get("available_apps"), list) else []
        
        # Build context-aware system prompt with AI enhancements
        context_summary = self._build_enhanced_context_summary(context)
        
        # Enhanced system prompt with better examples
        system_prompt = (
            f"You are {self.system_context['assistant_name']}, a highly intelligent AI assistant with full system access.\n\n"
            "CAPABILITIES:\n"
            f"- Open/control any application: {', '.join(available_apps[:10])}... (and many more)\n"
            "- Send WhatsApp messages to contacts\n"
            "- Control mouse and keyboard (click, type, shortcuts)\n"
            "- Web searches and browsing\n"
            "- File operations\n"
            "- Casual conversation and questions\n\n"
            "CONTEXT:\n"
            f"{context_summary}\n\n"
            "INSTRUCTIONS:\n"
            "1. For casual conversation (greetings, questions, chat), respond naturally\n"
            "2. For system commands, determine the appropriate action AND provide a natural response\n"
            "3. For multi-step commands (e.g., 'open word and write about X'), break into steps\n"
            "4. Always be helpful, context-aware, and learn from user patterns\n\n"
            "EXAMPLES:\n"
            'User: "open firefox" -> {"response_text": "Opening Firefox for you!", "intent": "system_control", "action": "open", "parameters": {"application": "firefox"}}\n'
            'User: "open word and write about AI" -> {"response_text": "Opening Word and preparing to write about AI!", "intent": "multi_step", "action": "open_and_execute", "parameters": {"application": "word", "task": "write", "topic": "AI"}}\n\n'
            "Respond with JSON in this format:\n"
            "{\n"
            '    "response_text": "Your natural conversational response",\n'
            '    "intent": "conversation|system_control|multi_step|whatsapp_send|web_search|file_operation|keyboard_mouse",\n'
            '    "action": "specific action if needed",\n'
            '    "parameters": {"application": "app_name", "task": "task_type", "content": "content_to_generate"},\n'
            '    "is_conversational": true\n'
            "}"
        )

        try:
            response = self.generate_response(system_prompt, user_input, max_tokens=300)
            
            # Parse JSON response with enhanced error handling
            parsed_response = self._parse_llm_response(response, user_input)
            
            # Add to legacy context (for compatibility)
            self.add_to_context("user", user_input)
            self.add_to_context("assistant", parsed_response.get("response_text", ""))
            
            return parsed_response
            
        except Exception as e:
            self.logger.error(f"Generation error: {e}")
            return self._generate_error_response(user_input)
    
    def _build_enhanced_context_summary(self, context: Dict[str, Any]) -> str:
        """Build enhanced context summary with AI insights"""
        summary_parts = []
        
        # Recent interactions
        recent_interactions = context.get("recent_interactions", [])
        if recent_interactions:
            summary_parts.append("RECENT CONVERSATION:")
            for interaction in recent_interactions[-3:]:
                summary_parts.append(f"User: {interaction.get('user_input', '')}")
                summary_parts.append(f"Assistant: {interaction.get('assistant_response', '')}")
        
        # System state
        system_state = context.get("system_state", {})
        if system_state.get("running_apps"):
            summary_parts.append(f"RUNNING APPS: {', '.join(system_state['running_apps'][:5])}")
        
        # AI recommendations
        if context.get("ai_recommendations"):
            summary_parts.append("AI INSIGHTS:")
            summary_parts.extend(context["ai_recommendations"])
        
        # Usage patterns
        usage_patterns = context.get("usage_patterns", {})
        if usage_patterns:
            top_apps = sorted(usage_patterns.items(), key=lambda x: x[1].get("count", 0), reverse=True)[:3]
            if top_apps:
                summary_parts.append(f"FREQUENTLY USED: {', '.join([app for app, _ in top_apps])}")
        
        return "\n".join(summary_parts)
    
    def _parse_llm_response(self, response: str, user_input: str) -> Dict[str, Any]:
        """Parse LLM response with enhanced error handling"""
        
        # Try to extract JSON
        if '{' in response and '}' in response:
            start = response.find('{')
            end = response.rfind('}') + 1
            json_str = response[start:end]
            
            try:
                parsed = json.loads(json_str)
                
                # Validate and set defaults
                if isinstance(parsed, dict):
                    parsed.setdefault("response_text", "I'm ready to help!")
                    parsed.setdefault("intent", "conversation")
                    parsed.setdefault("action", None)
                    parsed.setdefault("parameters", {})
                    parsed.setdefault("is_conversational", True)
                    
                    return parsed
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parse error: {e}")
                self.logger.debug(f"Failed JSON: {json_str}")
        
        # Fallback: create structured response from raw text
        return {
            "response_text": response.strip(),
            "intent": "conversation",
            "action": None,
            "parameters": {},
            "is_conversational": True
        }
    
    def _learn_from_interaction(self, user_input: str, response: Dict[str, Any], 
                               intent_analysis: Dict[str, Any]):
        """Learn from user interactions for continuous improvement"""
        
        # Determine success based on response completeness and intent confidence
        success = (
            response.get("intent") != "conversation" or 
            intent_analysis.get("confidence", 0) > 0.7
        )
        
        # Add to enhanced context for learning
        self.enhanced_context.add_interaction(
            user_input=user_input,
            assistant_response=response.get("response_text", ""),
            intent=intent_analysis,
            success=success
        )
    
    def _generate_error_response(self, user_input: str) -> Dict[str, Any]:
        """Generate error response with learning capability"""
        error_response = "I'm having trouble processing that. Could you try rephrasing?"
        
        # Add to context for learning
        self.add_to_context("user", user_input)
        self.add_to_context("assistant", error_response)
        
        return {
            "response_text": error_response,
            "intent": "conversation",
            "action": None,
            "parameters": {},
            "is_conversational": True,
            "error": True
        }
    
    def learn_from_correction(self, original_command: str, corrected_command: str):
        """Learn from user corrections"""
        self.voice_optimizer.add_correction(original_command, corrected_command)
        self.intent_parser.learn_from_correction(original_command, corrected_command)
        self.logger.info(f"Learned correction: '{original_command}' -> '{corrected_command}'")
    
    def get_ai_stats(self) -> Dict[str, Any]:
        """Get AI learning statistics"""
        return {
            "voice_optimization": self.voice_optimizer.get_optimization_stats(),
            "context_management": {
                "interactions_tracked": len(self.enhanced_context.conversation_history),
                "apps_learned": len(self.enhanced_context.app_usage_patterns),
                "success_rate_tracked": len(self.enhanced_context.command_success_rates)
            },
            "recommendations_available": len(self.enhanced_context.get_recommendations())
        }
    
    def generate_response(self, system_prompt: str, user_input: str, max_tokens: int = 256) -> str:
        """Generate raw response from Ollama"""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        
        full_prompt = f"System: {system_prompt}\nUser: {user_input}\nAssistant:"
        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=60)
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json().get("response", "").strip()
            if not result:
                raise Exception("Empty response from Ollama")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {e}")
            raise Exception(f"Failed to connect to Ollama: {e}")
        except Exception as e:
            self.logger.error(f"Ollama generation error: {e}")
            raise
    
    def clear_context(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.enhanced_context = EnhancedContextManager()  # Reset enhanced context
        self.logger.info("All conversation context cleared")
