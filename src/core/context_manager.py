import json
import logging
import os,sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque

class EnhancedContextManager:
    def __init__(self, max_history: int = 50):
        self.logger = logging.getLogger(__name__)
        self.max_history = max_history
        
        # Context storage
        self.conversation_history = deque(maxlen=max_history)
        self.system_state = {
            "running_apps": [],
            "current_window": None,
            "recent_commands": deque(maxlen=20),
            "user_preferences": {},
            "environment_info": self._get_environment_info()
        }
        
        # AI learning data
        self.command_success_rates = {}
        self.app_usage_patterns = {}
        self.user_behavior_patterns = {
            "most_active_hours": [],
            "command_frequency": {},
            "error_patterns": []
        }
        
        # Load persistent data
        self._load_persistent_data()
        
    def add_interaction(self, user_input: str, assistant_response: str, 
                       intent: Dict[str, Any], success: bool = True):
        """Add interaction to context with comprehensive tracking"""
        interaction = {
            "timestamp": datetime.now(),
            "user_input": user_input,
            "assistant_response": assistant_response,
            "intent": intent,
            "success": success,
            "session_info": self._get_session_info()
        }
        
        self.conversation_history.append(interaction)
        self._update_learning_data(user_input, success, intent)
        self._save_interaction_to_persistence(interaction)
        
    def get_current_context(self) -> Dict[str, Any]:
        """Get comprehensive current context with AI insights"""
        return {
            "recent_interactions": list(self.conversation_history)[-5:],
            "system_state": self.system_state.copy(),
            "success_rates": dict(self.command_success_rates),
            "usage_patterns": dict(self.app_usage_patterns),
            "behavior_patterns": self.user_behavior_patterns.copy(),
            "context_summary": self._generate_context_summary(),
            "ai_insights": self._generate_ai_insights(),
            "session_stats": self._get_session_stats()
        }
    
    def update_system_state(self, key: str, value: Any):
        """Update system state with automatic learning"""
        old_value = self.system_state.get(key)
        self.system_state[key] = value
        
        # Track state changes for learning
        if key == "running_apps" and old_value != value:
            self._track_app_state_change(
                old_value if isinstance(old_value, list) else None,
                value if isinstance(value, list) else None
            )

        
        self.logger.debug(f"Updated system state: {key} = {value}")
    
    def _update_learning_data(self, command: str, success: bool, intent: Dict[str, Any]):
        """Update all learning data structures"""
        # Update success rates
        self._update_success_rates(command, success)
        
        # Update usage patterns
        self._update_usage_patterns(intent)
        
        # Update behavior patterns
        self._update_behavior_patterns(command, success)
    
    def _update_success_rates(self, command: str, success: bool):
        """Track command success rates with pattern recognition"""
        command_key = self._normalize_command(command)
        
        if command_key not in self.command_success_rates:
            self.command_success_rates[command_key] = {
                "successes": 0, 
                "attempts": 0, 
                "recent_attempts": deque(maxlen=10),
                "first_seen": datetime.now()
            }
        
        self.command_success_rates[command_key]["attempts"] += 1
        self.command_success_rates[command_key]["recent_attempts"].append({
            "success": success,
            "timestamp": datetime.now()
        })
        
        if success:
            self.command_success_rates[command_key]["successes"] += 1
    
    def _update_usage_patterns(self, intent: Dict[str, Any]):
        """Track comprehensive app usage patterns"""
        if intent.get("intent") == "system_control" and intent.get("target"):
            app = intent["target"]
            current_time = datetime.now()
            
            if app not in self.app_usage_patterns:
                self.app_usage_patterns[app] = {
                    "count": 0,
                    "last_used": None,
                    "usage_times": [],
                    "success_rate": 1.0,
                    "common_tasks": []
                }
            
            pattern = self.app_usage_patterns[app]
            pattern["count"] += 1
            pattern["last_used"] = current_time
            pattern["usage_times"].append(current_time)
            
            # Keep only recent usage times (last 30 days)
            cutoff = current_time - timedelta(days=30)
            pattern["usage_times"] = [t for t in pattern["usage_times"] if t > cutoff]
            
            # Track common tasks
            if intent.get("steps"):
                for step in intent["steps"]:
                    task = step.get("task_type")
                    if task and task not in pattern["common_tasks"]:
                        pattern["common_tasks"].append(task)
    
    def _update_behavior_patterns(self, command: str, success: bool):
        """Track user behavior patterns for AI insights"""
        current_hour = datetime.now().hour
        
        # Track active hours
        if current_hour not in self.user_behavior_patterns["most_active_hours"]:
            self.user_behavior_patterns["most_active_hours"].append(current_hour)
        
        # Track command frequency
        cmd_normalized = self._normalize_command(command)
        freq = self.user_behavior_patterns["command_frequency"]
        freq[cmd_normalized] = freq.get(cmd_normalized, 0) + 1
        
        # Track error patterns
        if not success:
            error_pattern = {
                "command": command,
                "timestamp": datetime.now(),
                "hour": current_hour
            }
            self.user_behavior_patterns["error_patterns"].append(error_pattern)
            
            # Keep only recent errors (last 50)
            if len(self.user_behavior_patterns["error_patterns"]) > 50:
                self.user_behavior_patterns["error_patterns"] = \
                    self.user_behavior_patterns["error_patterns"][-50:]
    
    def _track_app_state_change(self, old_apps: Optional[List[str]], new_apps: Optional[List[str]]):
        """Track when apps are opened/closed for context"""
        if old_apps is None:
            old_apps = []
        if new_apps is None:
            new_apps = []
            
        opened_apps = set(new_apps) - set(old_apps)
        closed_apps = set(old_apps) - set(new_apps)
        
        for app in opened_apps:
            self.logger.info(f"App opened: {app}")
            
        for app in closed_apps:
            self.logger.info(f"App closed: {app}")

    
    def _generate_context_summary(self) -> str:
        """Generate AI-powered context summary"""
        parts = []
        
        # Recent app usage
        recent_apps = self._get_recently_used_apps(minutes=30)
        if recent_apps:
            parts.append(f"Recently used: {', '.join(recent_apps[:3])}")
        
        # Current productivity patterns
        if self._is_productive_session():
            parts.append("High productivity session detected")
        
        # Success rate trends
        avg_success = self._get_average_success_rate()
        if avg_success < 0.7:
            parts.append("Voice recognition may need improvement")
        elif avg_success > 0.9:
            parts.append("Excellent command recognition")
        
        return " | ".join(parts) if parts else "Starting fresh session"
    
    def _generate_ai_insights(self) -> List[str]:
        """Generate AI-powered insights about user behavior"""
        insights = []
        
        # Usage pattern insights
        if self.app_usage_patterns:
            try:
                most_used = max(self.app_usage_patterns.items(), 
                            key=lambda x: x[1]["count"])
                if isinstance(most_used, tuple) and len(most_used) == 2:
                    app_name, app_data = most_used
                    if isinstance(app_data, dict) and "count" in app_data:
                        insights.append(f"Most used app: {app_name} ({app_data['count']} times)")
            except (ValueError, KeyError, TypeError) as e:
                self.logger.debug(f"Error getting most used app: {e}")

        
        # Time-based insights
        active_hours = self.user_behavior_patterns["most_active_hours"]
        if active_hours:
            avg_hour = sum(active_hours) // len(active_hours)
            if 9 <= avg_hour <= 17:
                insights.append("Primary usage during work hours")
            elif 18 <= avg_hour <= 23:
                insights.append("Primary usage in the evening")
        
        # Performance insights
        error_rate = len(self.user_behavior_patterns["error_patterns"]) / max(1, len(self.conversation_history))
        if error_rate > 0.3:
            insights.append("Consider voice training or clearer pronunciation")
        
        return insights
    
    def get_recommendations(self) -> List[str]:
        """Get AI-powered recommendations"""
        recommendations = []
        
        # App recommendations based on usage
        try:
            frequent_apps = sorted(self.app_usage_patterns.items(), 
                                key=lambda x: x[1].get("count", 0), reverse=True)[:3]
            
            if frequent_apps:
                app_names = []
                for item in frequent_apps:
                    if isinstance(item, tuple) and len(item) >= 1:
                        app_names.append(item[0])
                
                if app_names:
                    recommendations.append(f"Quick access: {', '.join(app_names)}")
        except (ValueError, KeyError, TypeError) as e:
            self.logger.debug(f"Error getting frequent apps: {e}")

        
        # Productivity recommendations
        if self._should_suggest_break():
            recommendations.append("Consider taking a break - you've been active for a while")
        
        # Learning recommendations
        low_success_commands = self._get_low_success_commands()
        if low_success_commands:
            recommendations.append(f"Practice these commands: {', '.join(low_success_commands[:2])}")
        
        return recommendations
    
    def _get_recently_used_apps(self, minutes: int = 30) -> List[str]:
        """Get apps used in the last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = []
        
        for app, data in self.app_usage_patterns.items():
            if data["last_used"] and data["last_used"] > cutoff:
                recent.append(app)
        
        return recent
    
    def _is_productive_session(self) -> bool:
        """Determine if current session shows high productivity"""
        if len(self.conversation_history) < 5:
            return False
        
        recent_interactions = list(self.conversation_history)[-10:]
        successful_actions = sum(1 for i in recent_interactions 
                               if i["success"] and i["intent"].get("intent") != "conversation")
        
        return successful_actions >= 3
    
    def _get_average_success_rate(self) -> float:
        """Calculate overall success rate"""
        if not self.command_success_rates:
            return 0.8  # Default assumption
        
        total_attempts = sum(data["attempts"] for data in self.command_success_rates.values())
        total_successes = sum(data["successes"] for data in self.command_success_rates.values())
        
        return total_successes / max(1, total_attempts)
    
    def _should_suggest_break(self) -> bool:
        """Suggest break based on usage patterns"""
        if len(self.conversation_history) < 20:
            return False
        
        # Check if user has been active for more than 2 hours
        first_interaction = self.conversation_history[0]["timestamp"]
        time_active = datetime.now() - first_interaction
        
        return time_active > timedelta(hours=2)
    
    def _get_low_success_commands(self) -> List[str]:
        """Get commands with low success rates"""
        low_success = []
        
        for cmd, data in self.command_success_rates.items():
            if data["attempts"] >= 3:  # Only consider commands tried multiple times
                success_rate = data["successes"] / data["attempts"]
                if success_rate < 0.5:
                    low_success.append(cmd)
        
        return low_success[:3]  # Return top 3
    
    def _normalize_command(self, command: str) -> str:
        """Normalize commands for consistent tracking"""
        # Remove common variations
        normalized = command.lower().strip()
        normalized = ' '.join(normalized.split())  # Remove extra spaces
        
        # Group similar commands
        if any(word in normalized for word in ["open", "launch", "start"]):
            words = normalized.split()
            if len(words) >= 2:
                return f"open_{words[-1]}"  # "open_firefox", "launch_word" -> "open_firefox"
        
        return normalized
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get system environment information"""
        return {
            "platform": os.name,
            "session_start": datetime.now(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}"
        }
    
    def _get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        return {
            "session_length": len(self.conversation_history),
            "current_time": datetime.now(),
            "day_of_week": datetime.now().strftime("%A"),
            "hour": datetime.now().hour
        }
    
    def _get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        if not self.conversation_history:
            return {"total_interactions": 0}
        
        interactions = list(self.conversation_history)
        successful = sum(1 for i in interactions if i["success"])
        
        return {
            "total_interactions": len(interactions),
            "successful_interactions": successful,
            "success_rate": successful / len(interactions),
            "session_duration": str(datetime.now() - interactions[0]["timestamp"]),
            "unique_intents": len(set(i["intent"].get("intent", "unknown") for i in interactions))
        }
    
    def _load_persistent_data(self):
        """Load learning data from persistent storage"""
        try:
            # This could load from a file in the future
            # For now, start fresh each session
            pass
        except Exception as e:
            self.logger.error(f"Failed to load persistent data: {e}")
    
    def _save_interaction_to_persistence(self, interaction: Dict[str, Any]):
        """Save interaction for future learning (privacy-aware)"""
        try:
            # In the future, implement privacy-safe persistence
            # For now, only store in memory
            pass
        except Exception as e:
            self.logger.error(f"Failed to save interaction: {e}")
