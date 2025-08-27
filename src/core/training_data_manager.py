import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from collections import defaultdict

class TrainingDataManager:
    def __init__(self, data_file: str = "config/training_data.json"):
        self.logger = logging.getLogger(__name__)
        self.data_file = data_file
        
        # Initialize training data structure
        self.training_data = {
            "command_variations": {},
            "intent_templates": {},
            "expected_behaviors": {},
            "failure_cases": {},
            "user_patterns": {},
            "last_updated": None
        }
        
        # Load existing data
        self._load_training_data()
        
        # Initialize base templates
        self._initialize_base_templates()
    
    def _load_training_data(self):
        """Load existing training data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    self.training_data.update(loaded_data)
                    self.logger.info(f"Loaded training data from {self.data_file}")
        except Exception as e:
            self.logger.warning(f"Could not load training data: {e}")
    
    def _save_training_data(self):
        """Save training data to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            self.training_data["last_updated"] = datetime.now().isoformat()
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.training_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Saved training data to {self.data_file}")
        except Exception as e:
            self.logger.error(f"Could not save training data: {e}")
    
    def _initialize_base_templates(self):
        """Initialize base command templates if not present"""
        
        if not self.training_data["intent_templates"]:
            self.training_data["intent_templates"] = {
                "system_control": {
                    "patterns": [
                        "{action} {app}",
                        "{action} the {app}",
                        "can you {action} {app}",
                        "please {action} {app} for me",
                        "I need you to {action} {app}",
                        "could you {action} {app} please"
                    ],
                    "actions": ["open", "launch", "start", "run", "fire up", "boot up"],
                    "variations": {
                        "open": ["launch", "start", "run", "fire up", "boot up", "initialize"],
                        "close": ["quit", "exit", "shut down", "terminate", "kill", "end"],
                        "minimize": ["hide", "shrink", "reduce"],
                        "maximize": ["expand", "enlarge", "full screen", "make bigger"]
                    }
                },
                "multi_step": {
                    "patterns": [
                        "{action} {app} and {secondary_action}",
                        "{action} {app} then {secondary_action}",
                        "open {app} and {secondary_action}",
                        "launch {app} and {secondary_action}",
                        "start {app} and {secondary_action}"
                    ],
                    "secondary_actions": [
                        "write about {topic}",
                        "create a document about {topic}",
                        "make a file about {topic}",
                        "type something about {topic}",
                        "write a paragraph on {topic}"
                    ]
                },
                "web_search": {
                    "patterns": [
                        "search for {query}",
                        "google {query}",
                        "find information about {query}",
                        "look up {query}",
                        "search the web for {query}"
                    ]
                }
            }
        
        if not self.training_data["expected_behaviors"]:
            self.training_data["expected_behaviors"] = {
                "system_control": {
                    "open_application": {
                        "steps": [
                            "parse_app_name",
                            "find_executable",
                            "launch_process",
                            "wait_for_window",
                            "confirm_success"
                        ],
                        "success_criteria": ["application_running", "window_visible"],
                        "failure_modes": ["app_not_found", "launch_failed", "timeout"],
                        "recovery_actions": ["suggest_similar", "manual_browse", "install_prompt"]
                    }
                },
                "multi_step": {
                    "open_and_write": {
                        "steps": [
                            "open_application",
                            "wait_for_ready",
                            "generate_content",
                            "type_content",
                            "confirm_completion"
                        ],
                        "success_criteria": ["app_open", "content_generated", "text_typed"],
                        "failure_modes": ["app_fail", "generation_fail", "typing_fail"],
                        "recovery_actions": ["retry_open", "fallback_content", "manual_type"]
                    }
                }
            }
        
        # Save initialized templates
        self._save_training_data()
    
    def collect_command_variations(self, base_command: str, intent_type: str) -> List[str]:
        """Generate variations of a base command"""
        
        variations = []
        templates = self.training_data["intent_templates"].get(intent_type, {})
        patterns = templates.get("patterns", [])
        
        # Extract components from base command
        components = self._parse_command_components(base_command)
        
        # Generate variations using templates
        for pattern in patterns:
            try:
                variation = pattern.format(**components)
                variations.append(variation)
            except KeyError as e:
                self.logger.debug(f"Missing component {e} for pattern {pattern}")
        
        # Add action variations
        if "action" in components and intent_type in self.training_data["intent_templates"]:
            action_variations = self.training_data["intent_templates"][intent_type].get("variations", {})
            original_action = components["action"]
            
            if original_action in action_variations:
                for alt_action in action_variations[original_action]:
                    alt_components = components.copy()
                    alt_components["action"] = alt_action
                    
                    for pattern in patterns:
                        try:
                            variation = pattern.format(**alt_components)
                            variations.append(variation)
                        except KeyError:
                            continue
        
        # Store variations for future reference
        if base_command not in self.training_data["command_variations"]:
            self.training_data["command_variations"][base_command] = []
        
        self.training_data["command_variations"][base_command].extend(variations)
        self._save_training_data()
        
        return list(set(variations))  # Remove duplicates
    
    def _parse_command_components(self, command: str) -> Dict[str, str]:
        """Parse command into components (action, app, etc.)"""
        
        components = {}
        words = command.lower().split()
        
        # Common actions
        actions = ["open", "launch", "start", "run", "close", "quit", "exit"]
        for action in actions:
            if action in words:
                components["action"] = action
                break
        
        # Try to identify app name (usually after action)
        if "action" in components:
            action_index = words.index(components["action"])
            if action_index + 1 < len(words):
                # Take next word(s) as app name
                remaining_words = words[action_index + 1:]
                # Remove common words
                filtered_words = [w for w in remaining_words if w not in ["the", "a", "an", "and", "then"]]
                if filtered_words:
                    components["app"] = " ".join(filtered_words[:2])  # Take up to 2 words
        
        # Look for secondary actions (after "and" or "then")
        if "and" in words:
            and_index = words.index("and")
            secondary_part = " ".join(words[and_index + 1:])
            components["secondary_action"] = secondary_part
        elif "then" in words:
            then_index = words.index("then")
            secondary_part = " ".join(words[then_index + 1:])
            components["secondary_action"] = secondary_part
        
        return components
    
    def generate_expected_behaviors(self, intent_type: str, action: str) -> Dict[str, Any]:
        """Generate expected behavior definition for an intent-action pair"""
        
        behavior_key = f"{intent_type}_{action}"
        
        if behavior_key in self.training_data["expected_behaviors"]:
            return self.training_data["expected_behaviors"][behavior_key]
        
        # Generate basic behavior template
        behavior = {
            "steps": ["parse_intent", "execute_action", "confirm_result"],
            "success_criteria": ["intent_understood", "action_completed"],
            "failure_modes": ["parse_error", "execution_error"],
            "recovery_actions": ["retry", "clarify", "fallback"],
            "confidence_threshold": 0.7,
            "timeout_seconds": 30
        }
        
        # Customize based on intent type
        if intent_type == "system_control":
            behavior["steps"] = ["find_app", "launch_process", "verify_running"]
            behavior["success_criteria"] = ["app_found", "process_started", "window_visible"]
            behavior["failure_modes"] = ["app_not_found", "launch_failed", "timeout"]
            
        elif intent_type == "multi_step":
            behavior["steps"] = ["parse_steps", "execute_sequence", "verify_each_step"]
            behavior["success_criteria"] = ["all_steps_parsed", "sequence_completed"]
            behavior["failure_modes"] = ["step_failed", "sequence_interrupted"]
        
        # Store generated behavior
        self.training_data["expected_behaviors"][behavior_key] = behavior
        self._save_training_data()
        
        return behavior
    
    def add_user_interaction(self, command: str, intent: Dict[str, Any], success: bool, context: Dict[str, Any]):
        """Add user interaction to training data"""
        
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "intent": intent,
            "success": success,
            "context": context
        }
        
        # Categorize by success/failure
        if success:
            if "successful_interactions" not in self.training_data:
                self.training_data["successful_interactions"] = []
            self.training_data["successful_interactions"].append(interaction)
        else:
            if "failed_interactions" not in self.training_data:
                self.training_data["failed_interactions"] = []
            self.training_data["failed_interactions"].append(interaction)
        
        # Update user patterns
        user_id = context.get("user_id", "default_user")
        if user_id not in self.training_data["user_patterns"]:
            self.training_data["user_patterns"][user_id] = {
                "common_commands": defaultdict(int),
                "preferred_apps": defaultdict(int),
                "success_rate": {"total": 0, "successful": 0}
            }
        
        user_pattern = self.training_data["user_patterns"][user_id]
        user_pattern["common_commands"][command.lower()] += 1
        user_pattern["success_rate"]["total"] += 1
        
        if success:
            user_pattern["success_rate"]["successful"] += 1
        
        if intent.get("target"):
            user_pattern["preferred_apps"][intent["target"]] += 1
        
        # Save periodically (every 10 interactions)
        if len(self.training_data.get("successful_interactions", [])) + len(self.training_data.get("failed_interactions", [])) % 10 == 0:
            self._save_training_data()
    
    def get_command_suggestions(self, partial_command: str, limit: int = 5) -> List[str]:
        """Get command suggestions based on training data"""
        
        suggestions = []
        partial_lower = partial_command.lower()
        
        # Search through successful interactions
        for interaction in self.training_data.get("successful_interactions", []):
            command = interaction["command"]
            if partial_lower in command.lower():
                suggestions.append(command)
        
        # Search through command variations
        for base_command, variations in self.training_data["command_variations"].items():
            if partial_lower in base_command.lower():
                suggestions.append(base_command)
            
            for variation in variations:
                if partial_lower in variation.lower():
                    suggestions.append(variation)
        
        # Remove duplicates and limit results
        unique_suggestions = list(set(suggestions))
        return unique_suggestions[:limit]
    
    def export_training_dataset(self, format: str = "json", output_file: Optional[str] = None) -> str:
        """Export training dataset in specified format"""
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"training_dataset_{timestamp}.{format}"
        
        try:
            if format == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(self.training_data, f, indent=2, ensure_ascii=False)
            
            elif format == "csv":
                import csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Write successful interactions
                    writer.writerow(["command", "intent", "success", "timestamp"])
                    for interaction in self.training_data.get("successful_interactions", []):
                        writer.writerow([
                            interaction["command"],
                            json.dumps(interaction["intent"]),
                            interaction["success"],
                            interaction["timestamp"]
                        ])
            
            self.logger.info(f"Exported training dataset to {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Failed to export training dataset: {e}")
            return ""
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get statistics about training data"""
        
        stats = {
            "total_interactions": len(self.training_data.get("successful_interactions", [])) + len(self.training_data.get("failed_interactions", [])),
            "successful_interactions": len(self.training_data.get("successful_interactions", [])),
            "failed_interactions": len(self.training_data.get("failed_interactions", [])),
            "command_variations": len(self.training_data["command_variations"]),
            "intent_templates": len(self.training_data["intent_templates"]),
            "expected_behaviors": len(self.training_data["expected_behaviors"]),
            "unique_users": len(self.training_data.get("user_patterns", {}))
        }
        
        if stats["total_interactions"] > 0:
            success_ratio = (stats["successful_interactions"] / stats["total_interactions"]) * 100
            stats["success_rate"] = int(success_ratio)  # Keep as float with 3 decimal places
        else:
            stats["success_rate"] = 0 # Explicitly float
        
        return stats

