import re
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

class AdvancedIntentParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Enhanced intent patterns
        self.intent_patterns = {
            "system_control": [
                r"(open|launch|start|run)\s+(\w+)",
                r"(close|exit|quit)\s+(\w+)",
                r"(minimize|maximize)\s+(\w+)"
            ],
            "multi_step": [
                r"(open|launch)\s+(\w+)\s+(and|then)\s+(.+)",
                r"(create|make|write)\s+(.+)\s+(in|with|using)\s+(\w+)",
                r"(start|open)\s+(\w+)\s+(and|then)\s+(write|type|create)\s+(.+)"
            ],
            "web_search": [
                r"(search|google|find)\s+(for\s+)?(.+)",
                r"(look up|check)\s+(.+)",
                r"(browse|go to)\s+(.+)"
            ],
            "file_operation": [
                r"(create|make|new)\s+(file|folder|document)",
                r"(save|export)\s+(.+)\s+(as|to)\s+(.+)",
                r"(delete|remove)\s+(file|folder)\s+(.+)"
            ]
        }
        
        # App name mapping for better recognition
        self.app_aliases = {
            "word": "microsoft word",
            "excel": "microsoft excel",
            "chrome": "google chrome",
            "notepad": "notepad",
            "firefox": "mozilla firefox",
            "calculator": "calculator",
            "vs code": "visual studio code",
            "vscode": "visual studio code"
        }
        
        self.correction_history = []
        
    def parse_command(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Parse user command into structured intent with AI enhancement"""
        if context is None:
            context = {}

        user_input = user_input.strip().lower()
        
        self.logger.debug(f"Parsing command: '{user_input}'")
        
        # Check for multi-step commands first (most complex)
        multi_step = self._detect_multi_step(user_input)
        if multi_step:
            return self._plan_multi_step_execution(multi_step, context)
        
        # Single-step intent detection
        intent_result = self._classify_intent(user_input)
        return self._enhance_with_context(intent_result, context)
    
    def _detect_multi_step(self, command: str) -> Optional[Dict[str, Any]]:
        """Detect commands that require multiple steps"""
        for pattern in self.intent_patterns["multi_step"]:
            match = re.search(pattern, command)
            if match:
                groups = match.groups()
                return {
                    "type": "multi_step",
                    "primary_action": groups[0],  # open/launch
                    "target": self._normalize_app_name(groups[8]),  # app name
                    "connector": groups,  # and/then
                    "secondary_action": groups if len(groups) > 3 else None,  # what to do
                    "secondary_target": groups if len(groups) > 4 else None  # content/topic
                }
        return None
    
    def _classify_intent(self, command: str) -> Dict[str, Any]:
        """Classify single-step intents with confidence scoring"""
        best_match = {"intent": "conversation", "confidence": 0.3}
        
        for intent_type, patterns in self.intent_patterns.items():
            if intent_type == "multi_step":
                continue
                
            for pattern in patterns:
                match = re.search(pattern, command)
                if match:
                    groups = match.groups()
                    confidence = self._calculate_confidence(match, command)
                    
                    if confidence > best_match["confidence"]:
                        best_match = {
                            "intent": intent_type,
                            "action": groups[0],
                            "target": self._normalize_app_name(groups[8]) if len(groups) >= 2 else None,
                            "additional": groups if len(groups) >= 3 else None,
                            "confidence": confidence
                        }
        
        return best_match
    
    def _plan_multi_step_execution(self, multi_step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan execution for multi-step commands with AI enhancement"""
        steps = []
        
        # Step 1: Open/Launch application
        steps.append({
            "order": 1,
            "action": multi_step["primary_action"],
            "target": multi_step["target"],
            "type": "system_control",
            "description": f"{multi_step['primary_action']} {multi_step['target']}"
        })
        
        # Step 2: Execute secondary action
        if multi_step["secondary_action"]:
            step_2 = {
                "order": 2,
                "action": "execute_task",
                "task_type": multi_step["secondary_action"],
                "content": multi_step.get("secondary_target", ""),
                "type": "automation",
                "description": f"{multi_step['secondary_action']} content"
            }
            
            # Enhanced content generation for specific tasks
            if "write" in multi_step["secondary_action"] and multi_step.get("secondary_target"):
                step_2["content_to_generate"] = multi_step["secondary_target"]
                step_2["generation_type"] = "text"
            
            steps.append(step_2)
        
        return {
            "intent": "multi_step_execution",
            "steps": steps,
            "confidence": 0.85,
            "total_steps": len(steps),
            "estimated_time": len(steps) * 3  # Rough estimate in seconds
        }
    
    def _normalize_app_name(self, app_name: str) -> str:
        """Normalize app names using aliases"""
        if not app_name:
            return app_name
            
        normalized = app_name.lower().strip()
        return self.app_aliases.get(normalized, normalized)
    
    def _calculate_confidence(self, match, command: str) -> float:
        """Calculate confidence score for pattern matches"""
        base_confidence = 0.8
        
        # Boost confidence for exact matches
        if match.group(0) == command.strip():
            base_confidence += 0.15
        
        # Boost for known app names
        groups = match.groups()
        if len(groups) >= 2 and groups[1] in self.app_aliases:
            base_confidence += 0.05
        
        return min(1.0, base_confidence)
    
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
            target = intent.get("target")
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
                # Likely an app name correction
                self.app_aliases[orig_word] = corr_word
                self.logger.info(f"Added app alias: {orig_word} -> {corr_word}")
