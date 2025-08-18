# Enhanced LLM Manager with Context & Conversation
import os
import logging
import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class ConversationalLLMManager:
    def __init__(self, model_name: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.is_loaded = False
        
        # Conversation context
        self.conversation_history = []
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
        except:
            return False
    
    def add_to_context(self, role: str, content: str):
        """Add message to conversation context"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep context manageable (last 20 messages)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def generate_conversational_response(self, user_input: str, available_apps: List[str]) -> Dict[str, Any]:
        """Generate both conversation response and action intent"""
        
        # Build context-aware system prompt
        context_summary = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in self.conversation_history[-6:]  # Last 6 messages for context
        ])
        
        system_prompt = f"""You are {self.system_context['assistant_name']}, a helpful AI assistant with full system access.

CAPABILITIES:
- Open/control any application: {', '.join(available_apps[:10])}... (and many more)
- Send WhatsApp messages to contacts
- Control mouse and keyboard (click, type, shortcuts)
- Web searches and browsing
- File operations
- Casual conversation and questions

RECENT CONVERSATION:
{context_summary}

INSTRUCTIONS:
1. Respond naturally and conversationally like a helpful human assistant
2. If this is casual conversation (greetings, questions, chat), respond warmly and naturally
3. If this is a system command, determine the appropriate action AND provide a natural response
4. Always be helpful, friendly, and context-aware
5. Keep responses concise but informative
6. If asked "how are you" or similar, respond naturally like a human would

Respond with JSON in this format:
{{
    "response_text": "Your natural conversational response",
    "intent": "conversation|system_control|whatsapp_send|web_search|file_operation|keyboard_mouse",
    "action": "specific action if needed",
    "parameters": {{"any": "relevant parameters"}},
    "is_conversational": true/false
}}"""

        try:
            response = self.generate_response(system_prompt, user_input, max_tokens=300)
            
            # Parse JSON response
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                parsed = json.loads(json_str)
                
                # Add to context
                self.add_to_context("user", user_input)
                self.add_to_context("assistant", parsed.get("response_text", ""))
                
                return parsed
            
            # Fallback for pure conversation
            return {
                "response_text": response,
                "intent": "conversation", 
                "action": None,
                "parameters": {},
                "is_conversational": True
            }
            
        except Exception as e:
            self.logger.error(f"Generation error: {e}")
            return {
                "response_text": "I'm having trouble processing that. Could you try again?",
                "intent": "conversation",
                "action": None, 
                "parameters": {},
                "is_conversational": True
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
        
        response = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=120)
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")
        
        return response.json().get("response", "").strip()
    
    def clear_context(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.logger.info("Conversation context cleared")
