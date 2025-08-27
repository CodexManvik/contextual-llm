import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import deque

class ConversationManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Conversation state tracking
        self.conversation_state = {
            "awaiting_clarification": False,
            "clarification_context": None,
            "last_intent": None,
            "retry_count": 0,
            "conversation_flow": deque(maxlen=10)
        }
        
        # Templates for different response types
        self.response_templates = {
            "clarification": {
                "multiple_apps": "I found multiple apps matching '{query}': {options}. Which one would you like?",
                "missing_info": "I need more information. {question}",
                "ambiguous_command": "I'm not sure what you mean by '{command}'. Could you be more specific?"
            },
            "error_recovery": {
                "app_launch_failed": "I couldn't open {app}. The application might not be installed or there was an error launching it.",
                "no_app_found": "I couldn't find an app called '{app}'. Would you like me to search for similar apps?",
                "command_failed": "Something went wrong with that command. Would you like to try again or try something else?"
            },
            "follow_up": {
                "success_next": "Successfully {action}. What would you like to do next?",
                "partial_completion": "I've completed the first part: {completed}. Should I continue with {next_step}?"
            }
        }
    
    def handle_clarification_request(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests for clarification when intent is ambiguous"""
        
        clarification_type = self._detect_clarification_type(user_input, context)
        
        if clarification_type == "app_selection":
            return self._handle_app_selection_clarification(user_input, context)
        elif clarification_type == "missing_parameter":
            return self._handle_missing_parameter_clarification(user_input, context)
        elif clarification_type == "ambiguous_action":
            return self._handle_ambiguous_action_clarification(user_input, context)
        
        return self._generate_generic_clarification(user_input, context)
    
    def _detect_clarification_type(self, user_input: str, context: Dict[str, Any]) -> str:
        """Detect what type of clarification is needed"""
        
        # Check if multiple apps were found
        if context.get("multiple_matches"):
            return "app_selection"
        
        # Check if required parameters are missing
        if context.get("missing_parameters"):
            return "missing_parameter"
        
        # Check if the action is ambiguous
        if context.get("ambiguous_intent"):
            return "ambiguous_action"
        
        return "generic"
    
    def _handle_app_selection_clarification(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle clarification when multiple apps match"""
        
        matches = context.get("multiple_matches", [])
        if not matches:
            return {"error": "No matches provided in context"}
        
        # Format options nicely
        if len(matches) <= 3:
            options = ", ".join(matches[:-1]) + f" or {matches[-1]}"
        else:
            options = ", ".join(matches[:3]) + f" and {len(matches)-3} more"
        
        response_text = self.response_templates["clarification"]["multiple_apps"].format(
            query=context.get("original_query", "that"),
            options=options
        )
        
        # Set conversation state
        self.conversation_state["awaiting_clarification"] = True
        self.conversation_state["clarification_context"] = {
            "type": "app_selection",
            "options": matches,
            "original_intent": context.get("original_intent")
        }
        
        return {
            "response_text": response_text,
            "intent": "clarification_request",
            "action": "await_user_selection",
            "parameters": {"options": matches},
            "is_conversational": True
        }
    
    def _handle_missing_parameter_clarification(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle clarification when required parameters are missing"""
        
        missing_params = context.get("missing_parameters", [])
        original_intent = context.get("original_intent", {})
        
        # Generate appropriate question based on missing parameter
        questions = {
            "topic": "What topic would you like me to write about?",
            "filename": "What should I name the file?",
            "content": "What content would you like me to add?",
            "app": "Which application would you like me to open?",
            "action": "What would you like me to do?"
        }
        
        # Pick the first missing parameter to ask about
        missing_param = missing_params[0] if missing_params else "information"
        question = questions.get(missing_param, f"What {missing_param} would you like?")
        
        response_text = self.response_templates["clarification"]["missing_info"].format(
            question=question
        )
        
        # Set conversation state
        self.conversation_state["awaiting_clarification"] = True
        self.conversation_state["clarification_context"] = {
            "type": "missing_parameter",
            "missing_param": missing_param,
            "original_intent": original_intent
        }
        
        return {
            "response_text": response_text,
            "intent": "clarification_request",
            "action": "await_parameter",
            "parameters": {"missing_parameter": missing_param},
            "is_conversational": True
        }
    
    def _handle_ambiguous_action_clarification(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle clarification when the action is ambiguous"""
        
        response_text = self.response_templates["clarification"]["ambiguous_command"].format(
            command=user_input
        )
        
        # Set conversation state
        self.conversation_state["awaiting_clarification"] = True
        self.conversation_state["clarification_context"] = {
            "type": "ambiguous_action",
            "original_command": user_input
        }
        
        return {
            "response_text": response_text,
            "intent": "clarification_request", 
            "action": "await_clarification",
            "parameters": {},
            "is_conversational": True
        }
    
    def _generate_generic_clarification(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic clarification request"""
        
        response_text = f"I'm not sure I understand. Could you rephrase that or be more specific?"
        
        return {
            "response_text": response_text,
            "intent": "clarification_request",
            "action": "await_clarification", 
            "parameters": {},
            "is_conversational": True
        }
    
    def process_clarification_response(self, user_response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user's response to a clarification request"""
        
        if not self.conversation_state["awaiting_clarification"]:
            return {"error": "No clarification was requested"}
        
        clarification_context = self.conversation_state["clarification_context"]
        
        if clarification_context["type"] == "app_selection":
            return self._process_app_selection_response(user_response, clarification_context)
        elif clarification_context["type"] == "missing_parameter":
            return self._process_missing_parameter_response(user_response, clarification_context)
        elif clarification_context["type"] == "ambiguous_action":
            return self._process_ambiguous_action_response(user_response, clarification_context)
        
        return {"error": "Unknown clarification type"}
    
    def _process_app_selection_response(self, user_response: str, clarification_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user's app selection response"""
        
        options = clarification_context.get("options", [])
        user_response_lower = user_response.lower().strip()
        
        # Find matching app
        selected_app = None
        for app in options:
            if user_response_lower in app.lower() or app.lower() in user_response_lower:
                selected_app = app
                break
        
        # Clear clarification state
        self.conversation_state["awaiting_clarification"] = False
        self.conversation_state["clarification_context"] = None
        
        if selected_app:
            # Reconstruct original intent with selected app
            original_intent = clarification_context.get("original_intent", {})
            original_intent["target"] = selected_app.lower()
            original_intent["parameters"] = original_intent.get("parameters", {})
            original_intent["parameters"]["application"] = selected_app.lower()
            
            return {
                "response_text": f"Got it! Opening {selected_app}.",
                "intent": original_intent.get("intent", "system_control"),
                "action": original_intent.get("action", "open"),
                "parameters": original_intent.get("parameters"),
                "target": selected_app.lower(),
                "is_conversational": False
            }
        else:
            return {
                "response_text": f"I couldn't find '{user_response}' in the options. Please try again.",
                "intent": "clarification_request",
                "action": "retry_selection",
                "parameters": {"options": options},
                "is_conversational": True
            }
    
    def _process_missing_parameter_response(self, user_response: str, clarification_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user's response to missing parameter question"""
        
        missing_param = clarification_context.get("missing_param")
        original_intent = clarification_context.get("original_intent", {})
        
        # Clear clarification state
        self.conversation_state["awaiting_clarification"] = False
        self.conversation_state["clarification_context"] = None
        
        # Add the missing parameter to the original intent
        if "parameters" not in original_intent:
            original_intent["parameters"] = {}
        
        original_intent["parameters"][missing_param] = user_response
        
        # Special handling for different parameter types
        if missing_param == "topic":
            original_intent["parameters"]["content_to_generate"] = user_response
            original_intent["parameters"]["generation_type"] = "text"
        
        return {
            "response_text": f"Perfect! I'll {original_intent.get('action', 'proceed')} with {user_response}.",
            "intent": original_intent.get("intent"),
            "action": original_intent.get("action"),
            "parameters": original_intent.get("parameters"),
            "target": original_intent.get("target"),
            "is_conversational": False
        }
    
    def _process_ambiguous_action_response(self, user_response: str, clarification_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user's clarification of ambiguous action"""
        
        # Clear clarification state
        self.conversation_state["awaiting_clarification"] = False
        self.conversation_state["clarification_context"] = None
        
        # Return the clarified command for re-parsing
        return {
            "response_text": "Thanks for clarifying! Let me process that.",
            "intent": "reparse_command",
            "action": "parse_clarified_command",
            "parameters": {"clarified_command": user_response},
            "is_conversational": False
        }
    
    def generate_error_recovery_response(self, error_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate appropriate error recovery responses"""
        
        app_name = context.get("app_name", "the application")
        
        if error_type == "app_launch_failed":
            response_text = self.response_templates["error_recovery"]["app_launch_failed"].format(
                app=app_name
            )
        elif error_type == "no_app_found":
            response_text = self.response_templates["error_recovery"]["no_app_found"].format(
                app=app_name
            )
        else:
            response_text = self.response_templates["error_recovery"]["command_failed"]
        
        return {
            "response_text": response_text,
            "intent": "error_recovery",
            "action": "inform_error",
            "parameters": {"error_type": error_type, "context": context},
            "is_conversational": True
        }
    
    def generate_follow_up_question(self, completed_action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate follow-up questions after successful actions"""
        
        # Simple follow-up for now
        response_text = self.response_templates["follow_up"]["success_next"].format(
            action=completed_action
        )
        
        return {
            "response_text": response_text,
            "intent": "follow_up",
            "action": "await_next_command",
            "parameters": {"last_action": completed_action},
            "is_conversational": True
        }
    
    def is_awaiting_clarification(self) -> bool:
        """Check if conversation manager is waiting for clarification"""
        return self.conversation_state["awaiting_clarification"]
    
    def get_conversation_state(self) -> Dict[str, Any]:
        """Get current conversation state"""
        return self.conversation_state.copy()
    
    def reset_conversation_state(self):
        """Reset conversation state"""
        self.conversation_state = {
            "awaiting_clarification": False,
            "clarification_context": None,
            "last_intent": None,
            "retry_count": 0,
            "conversation_flow": deque(maxlen=10)
        }
        
        self.logger.info("Conversation state reset")
