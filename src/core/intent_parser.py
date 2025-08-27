import re
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Try to import NVIDIA task classifier (optional dependency)
NVIDIA_CLASSIFIER_AVAILABLE = False
task_classifier = None

try:
    from models.nvidia_task_classifier import task_classifier as nvidia_task_classifier
    task_classifier = nvidia_task_classifier
    NVIDIA_CLASSIFIER_AVAILABLE = True
except ImportError:
    logging.getLogger(__name__).warning("NVIDIA task classifier not available, falling back to regex patterns")
except Exception as e:
    logging.getLogger(__name__).warning(f"Failed to initialize NVIDIA classifier: {e}, falling back to regex patterns")

class AdvancedIntentParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Fix the conversation patterns - these are too broad
        self.conversation_patterns = [
            r'\b(hello|hi|hey|good morning|good afternoon|good evening)\b',
            r'\b(how are you|hows it going|whats up|how do you do)\b',
            r'\b(thank you|thanks|bye|goodbye|see you)\b',
            r'\b(whats your name|who are you|tell me about yourself)\b',
            r'\b(can you help|help me|i need help)\b'
        ]
        
        # Fix system control patterns - add specific app names
        self.system_control_patterns = [
            r'\b(open|launch|start|run)\s+(.+?)(?:\s+(?:for|please|now|app|application))*\s*$',
            r'\b(close|exit|quit)\s+(.+?)(?:\s+(?:for|please|now|app|application))*\s*$',
            r'\b(minimize|maximize)\s+(.+?)(?:\s+(?:for|please|now|app|application))*\s*$'
        ]
        
        # Add app aliases with better matching
        self.app_aliases = {
            'notepad': ['notepad', 'text editor', 'note pad'],
            'firefox': ['firefox', 'fire fox', 'browser'],
            'chrome': ['chrome', 'google chrome', 'browser'],
            'word': ['word', 'microsoft word', 'ms word'],
            'excel': ['excel', 'microsoft excel', 'ms excel'],
            'calculator': ['calculator', 'calc'],
            'explorer': ['explorer', 'file explorer', 'files']
        }
        
        self.correction_history = []
        
    def parse_command(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Parse user command into structured intent with AI enhancement"""
        if context is None:
            context = {}

        user_input = user_input.strip()
        
        self.logger.debug(f"Parsing command: '{user_input}'")
        
        # Parse intent with error handling
        try:
            intent_result = self.parse_intent(user_input)
            return self._enhance_with_context(intent_result, context)
        except Exception as e:
            self.logger.error(f"Intent parsing failed: {e}")
            return {
                "intent": "unknown", 
                "confidence": 0.0,
                "error": str(e)
            }
    
    def parse_intent(self, user_input: str) -> Dict[str, Any]:
        """Enhanced intent parsing with NVIDIA classifier integration"""
        if not user_input or not user_input.strip():
            return {"intent": "unknown", "confidence": 0.0}
            
        user_input_clean = user_input.strip().lower()
        
        # First, try to use NVIDIA classifier if available
        if NVIDIA_CLASSIFIER_AVAILABLE:
            try:
                nvidia_result = self._parse_with_nvidia_classifier(user_input)
                if nvidia_result and nvidia_result.get("confidence", 0) > 0.6:
                    return nvidia_result
            except Exception as e:
                self.logger.warning(f"NVIDIA classifier failed: {e}, falling back to regex")
        
        # Fallback to regex patterns if NVIDIA classifier not available or failed
        return self._parse_with_regex_patterns(user_input_clean)
    
    def _parse_with_nvidia_classifier(self, user_input: str) -> Dict[str, Any]:
        """Parse intent using NVIDIA task classifier"""
        try:
            # Check if task_classifier is available
            if task_classifier is None:
                self.logger.warning("NVIDIA task classifier not initialized")
                return {"intent": "unknown", "confidence": 0.0}
            
            classification = task_classifier.classify_prompt(user_input)
            
            result = {
                "intent": classification["task_type"],
                "confidence": classification["confidence"],
                "complexity_score": classification["complexity_score"],
                "model_used": classification["model_used"],
                "detailed_analysis": classification["detailed_analysis"]
            }
            
            # Extract action and app name for system control intents
            if classification["task_type"] == "system_control":
                # Try to extract action and app name from the input
                action_match = re.search(r'\b(open|launch|start|close|quit|exit|minimize|maximize)\b', user_input.lower())
                app_match = re.search(r'\b(open|launch|start|close|quit|exit|minimize|maximize)\s+(\w+)', user_input.lower())
                
                if action_match:
                    result["action"] = action_match.group(1)
                
                if app_match and len(app_match.groups()) >= 2:
                    app_name = app_match.group(2)
                    result["app_name"] = self.resolve_app_alias(app_name)
                    result["original_app_name"] = app_name
            
            self.logger.info(f"NVIDIA classifier result: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in NVIDIA classifier parsing: {e}")
            return {"intent": "unknown", "confidence": 0.0}
    
    def _parse_with_regex_patterns(self, user_input_clean: str) -> Dict[str, Any]:
        """Fallback parsing using regex patterns"""
        # Check system control first (higher priority)
        for pattern in self.system_control_patterns:
            try:
                match = re.search(pattern, user_input_clean, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) >= 2:  # Ensure we have enough groups
                        action = groups[0]
                        app_name = groups[1].strip()
                        
                        # Resolve app aliases
                        resolved_app = self.resolve_app_alias(app_name)
                        
                        return {
                            "intent": "system_control",
                            "action": action,
                            "app_name": resolved_app,
                            "original_app_name": app_name,
                            "confidence": 0.9,
                            "context": {"command_type": "app_control"},
                            "model_used": "regex_patterns"
                        }
                    elif len(groups) == 1:  # Only app name provided
                        app_name = groups[0].strip()
                        resolved_app = self.resolve_app_alias(app_name)
                        
                        return {
                            "intent": "system_control", 
                            "action": "open",  # Default action
                            "app_name": resolved_app,
                            "original_app_name": app_name,
                            "confidence": 0.8,
                            "context": {"command_type": "app_control"},
                            "model_used": "regex_patterns"
                        }
            except Exception as e:
                self.logger.error(f"Error in pattern matching: {e}")
                continue
        
        # Single word app names (like "firefox")
        if user_input_clean in [alias for aliases in self.app_aliases.values() for alias in aliases]:
            resolved_app = self.resolve_app_alias(user_input_clean)
            return {
                "intent": "system_control",
                "action": "open",
                "app_name": resolved_app,
                "original_app_name": user_input_clean,
                "confidence": 0.9,
                "context": {"command_type": "app_control"},
                "model_used": "regex_patterns"
            }
        
        # Then check conversation patterns
        for pattern in self.conversation_patterns:
            try:
                if re.search(pattern, user_input_clean, re.IGNORECASE):
                    return {
                        "intent": "conversation", 
                        "confidence": 0.8,
                        "context": {"conversation_type": "greeting"},
                        "model_used": "regex_patterns"
                    }
            except Exception as e:
                self.logger.error(f"Error in conversation pattern matching: {e}")
                continue
        
        return {"intent": "unknown", "confidence": 0.0, "model_used": "regex_patterns"}
    
    def resolve_app_alias(self, app_name: str) -> str:
        """Resolve app aliases to canonical names"""
        app_name_lower = app_name.lower().strip()
        
        for canonical_name, aliases in self.app_aliases.items():
            if app_name_lower in [alias.lower() for alias in aliases]:
                return canonical_name
                
        return app_name_lower
    
    def _enhance_with_context(self, intent: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance intent with contextual information"""
        if context:
            # Add context-aware enhancements
            intent["context"] = {
                "current_apps": context.get("system_state", {}).get("running_apps", []),
                "recent_commands": context.get("system_state", {}).get("recent_commands", []),
                "user_preferences": context.get("system_state", {}).get("user_preferences", {})
            }
            
            # Boost confidence if app is recently used
            target = intent.get("app_name") or intent.get("target")
            if target and target in context.get("usage_patterns", {}):
                intent["confidence"] = min(1.0, intent.get("confidence", 0.5) + 0.1)
        
        return intent
    
    def learn_from_correction(self, original_command: str, corrected_command: str):
        """Learn from user corrections to improve future parsing"""
        correction = {
            "original": original_command,
            "corrected": corrected_command,
            "timestamp": datetime.now(),
            "pattern_learned": self._extract_pattern_difference(original_command, corrected_command)
        }
        
        self.correction_history.append(correction)
        
        # Update app aliases if needed
        self._update_aliases_from_correction(original_command, corrected_command)
        
        self.logger.info(f"Learning from correction: '{original_command}' -> '{corrected_command}'")
    
    def _extract_pattern_difference(self, original: str, corrected: str) -> str:
        """Extract what pattern changed in the correction"""
        # Simple difference detection
        orig_words = original.lower().split()
        corr_words = corrected.lower().split()
        
        if len(orig_words) == len(corr_words):
            for i, (o, c) in enumerate(zip(orig_words, corr_words)):
                if o != c:
                    return f"word_{i}: {o} -> {c}"
        
        return f"length_change: {len(orig_words)} -> {len(corr_words)}"
    
    def _update_aliases_from_correction(self, original: str, corrected: str):
        """Update app aliases based on corrections"""
        # Extract potential app names from corrections
        orig_words = original.lower().split()
        corr_words = corrected.lower().split()
        
        # Look for app name corrections
        for orig_word, corr_word in zip(orig_words, corr_words):
            if orig_word != corr_word and "open" in original:
                # Ensure the value is a list
                if orig_word in self.app_aliases:
                    self.app_aliases[orig_word].append(corr_word)
                else:
                    self.app_aliases[orig_word] = [corr_word]
                self.logger.info(f"Updated app alias: {orig_word} -> {corr_word}")
