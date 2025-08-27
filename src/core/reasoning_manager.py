"""
Reasoning Manager for the Autonomous AI Assistant
Enhances decision-making capabilities through intent classification, reasoning chains,
and adaptive learning with confidence scoring and contextual awareness.
"""
import re
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
from pathlib import Path


class IntentCategory(Enum):
    """Categories of user intents"""
    SYSTEM_CONTROL = "system_control"
    APPLICATION = "application"
    FILE_MANAGEMENT = "file_management"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"
    QUERY = "query"
    PERSONAL_ASSISTANT = "personal_assistant"
    SYSTEM_INFO = "system_info"
    UNKNOWN = "unknown"


class ConfidenceLevel(Enum):
    """Confidence levels for reasoning decisions"""
    VERY_HIGH = (0.9, 1.0)
    HIGH = (0.7, 0.9)
    MEDIUM = (0.5, 0.7)
    LOW = (0.3, 0.5)
    VERY_LOW = (0.0, 0.3)
    
    def contains(self, value: float) -> bool:
        return self.value[0] <= value < self.value[1]


@dataclass
class IntentResult:
    """Result of intent classification"""
    intent: str
    category: IntentCategory
    confidence: float
    entities: Dict[str, Any]
    context_score: float
    reasoning_chain: List[str]
    suggested_actions: List[str]
    timestamp: datetime


@dataclass
class ReasoningTrace:
    """Trace of reasoning steps"""
    input_text: str
    preprocessing_steps: List[str]
    feature_extraction: Dict[str, Any]
    classification_scores: Dict[str, float]
    context_analysis: Dict[str, Any]
    final_decision: IntentResult
    execution_time: float
    confidence_factors: Dict[str, float]


class ContextManager:
    """Manages conversation and system context"""
    
    def __init__(self, max_history: int = 50):
        self.conversation_history = deque(maxlen=max_history)
        self.user_preferences = {}
        self.session_context = {}
        self.system_state = {}
        
    def add_interaction(self, user_input: str, intent_result: IntentResult):
        """Add interaction to conversation history"""
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'user_input': user_input,
            'intent': intent_result.intent,
            'confidence': intent_result.confidence
        })
        
    def get_context_score(self, current_input: str) -> float:
        """Calculate context relevance score"""
        if not self.conversation_history:
            return 0.5
            
        # Analyze recent interactions
        recent_intents = [item['intent'] for item in list(self.conversation_history)[-5:]]
        current_keywords = self._extract_keywords(current_input)
        
        # Context continuity score
        continuity_score = 0.0
        if recent_intents:
            # Check for intent patterns
            if len(set(recent_intents[-3:])) == 1:  # Same intent repeated
                continuity_score += 0.3
            
        # Keyword similarity with recent interactions
        similarity_score = 0.0
        for item in list(self.conversation_history)[-3:]:
            prev_keywords = self._extract_keywords(item['user_input'])
            common_keywords = set(current_keywords) & set(prev_keywords)
            if common_keywords:
                similarity_score += len(common_keywords) / max(len(current_keywords), len(prev_keywords))
        
        return min(1.0, (continuity_score + similarity_score / 3) * 1.5)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        return [word for word in words if word not in stop_words and len(word) > 2]


class PatternMatcher:
    """Advanced pattern matching for intent classification"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.entity_patterns = self._initialize_entity_patterns()
        
    def _initialize_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize intent patterns with weights and contexts"""
        return {
            # System Control
            "shutdown_system": [
                {"pattern": r"\b(shutdown|turn off|power off)\b.*\b(computer|system|pc)\b", "weight": 0.9},
                {"pattern": r"\b(shut down|power down)\b", "weight": 0.8},
                {"pattern": r"\b(bye|goodbye).*\b(system|computer)\b", "weight": 0.7}
            ],
            "restart_system": [
                {"pattern": r"\b(restart|reboot)\b.*\b(computer|system|pc)\b", "weight": 0.9},
                {"pattern": r"\b(restart|reboot)\b", "weight": 0.8}
            ],
            "sleep_system": [
                {"pattern": r"\b(sleep|hibernate)\b.*\b(computer|system|pc)\b", "weight": 0.9},
                {"pattern": r"\b(put to sleep|go to sleep)\b", "weight": 0.8}
            ],
            
            # Application Control
            "open_application": [
                {"pattern": r"\b(open|launch|start|run)\b.*\b([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\b", "weight": 0.9},
                {"pattern": r"\b(execute|begin)\b.*\b([a-zA-Z]+)\b", "weight": 0.8}
            ],
            "close_application": [
                {"pattern": r"\b(close|quit|exit|end)\b.*\b([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\b", "weight": 0.9},
                {"pattern": r"\b(terminate|kill)\b.*\b([a-zA-Z]+)\b", "weight": 0.8}
            ],
            
            # File Management
            "create_file": [
                {"pattern": r"\b(create|make|new)\b.*\b(file|document)\b", "weight": 0.9},
                {"pattern": r"\b(generate|build)\b.*\b(file|document)\b", "weight": 0.8}
            ],
            "delete_file": [
                {"pattern": r"\b(delete|remove|erase)\b.*\b(file|document)\b", "weight": 0.9},
                {"pattern": r"\b(trash|discard)\b.*\b(file|document)\b", "weight": 0.8}
            ],
            "search_files": [
                {"pattern": r"\b(find|search|locate)\b.*\b(file|document|folder)\b", "weight": 0.9},
                {"pattern": r"\b(look for|where is)\b.*\b(file|document)\b", "weight": 0.8}
            ],
            
            # Communication
            "send_email": [
                {"pattern": r"\b(send|compose|write)\b.*\b(email|mail|message)\b", "weight": 0.9},
                {"pattern": r"\b(email|mail)\b.*\b(to|someone)\b", "weight": 0.8}
            ],
            "make_call": [
                {"pattern": r"\b(call|phone|dial)\b", "weight": 0.9},
                {"pattern": r"\b(ring|contact)\b.*\b(someone|person)\b", "weight": 0.8}
            ],
            
            # Automation
            "schedule_task": [
                {"pattern": r"\b(schedule|set)\b.*\b(reminder|alarm|task)\b", "weight": 0.9},
                {"pattern": r"\b(remind me|alert me)\b", "weight": 0.8}
            ],
            "automate_process": [
                {"pattern": r"\b(automate|auto)\b.*\b(process|task|workflow)\b", "weight": 0.9},
                {"pattern": r"\b(run automatically|do automatically)\b", "weight": 0.8}
            ],
            
            # Query/Information
            "get_weather": [
                {"pattern": r"\b(weather|temperature|forecast)\b", "weight": 0.9},
                {"pattern": r"\b(how hot|how cold|raining|sunny)\b", "weight": 0.8}
            ],
            "get_time": [
                {"pattern": r"\b(time|clock)\b.*\b(now|current)\b", "weight": 0.9},
                {"pattern": r"\b(what time|current time)\b", "weight": 0.9}
            ],
            "get_system_info": [
                {"pattern": r"\b(system|computer)\b.*\b(info|information|status|specs)\b", "weight": 0.9},
                {"pattern": r"\b(cpu|memory|disk|hardware)\b.*\b(usage|info|status)\b", "weight": 0.8}
            ],
            
            # Personal Assistant
            "set_reminder": [
                {"pattern": r"\b(remind|reminder)\b.*\b(me|to)\b", "weight": 0.9},
                {"pattern": r"\b(don't forget|remember)\b", "weight": 0.8}
            ],
            "take_note": [
                {"pattern": r"\b(note|write down|remember)\b.*\b(this|that)\b", "weight": 0.9},
                {"pattern": r"\b(save|store)\b.*\b(note|information)\b", "weight": 0.8}
            ]
        }
    
    def _initialize_entity_patterns(self) -> Dict[str, str]:
        """Initialize entity extraction patterns"""
        return {
            "application_name": r"\b(chrome|firefox|notepad|calculator|word|excel|powerpoint|spotify|steam|discord|zoom)\b",
            "file_name": r"['\"]([^'\"]+\.(txt|doc|pdf|jpg|png|mp4|zip|exe))['\"]",
            "time": r"\b(\d{1,2}:\d{2}(?:\s*[ap]m)?|\d{1,2}\s*[ap]m)\b",
            "date": r"\b(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|today|tomorrow|yesterday)\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}-?\d{3}-?\d{4}\b",
            "url": r"https?://[^\s]+",
            "number": r"\b\d+\b"
        }
    
    def match_intent(self, text: str) -> Tuple[str, float, Dict[str, Any]]:
        """Match text against intent patterns"""
        text_lower = text.lower()
        best_match = ("unknown", 0.0, {})
        
        for intent, patterns in self.patterns.items():
            max_score = 0.0
            entities = {}
            
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                weight = pattern_info["weight"]
                
                match = re.search(pattern, text_lower)
                if match:
                    # Base score from pattern weight
                    score = weight
                    
                    # Extract entities from the match
                    if match.groups():
                        entities.update(self._extract_entities_from_match(match, intent))
                    
                    # Bonus for multiple word matches
                    word_count = len(match.group().split())
                    if word_count > 1:
                        score += 0.1 * (word_count - 1)
                    
                    max_score = max(max_score, score)
            
            # Extract additional entities
            additional_entities = self._extract_entities(text)
            entities.update(additional_entities)
            
            if max_score > best_match[1]:
                best_match = (intent, max_score, entities)
        
        return best_match
    
    def _extract_entities_from_match(self, match, intent: str) -> Dict[str, Any]:
        """Extract entities specific to the matched intent"""
        entities = {}
        groups = match.groups()
        
        if intent in ["open_application", "close_application"] and groups:
            entities["application"] = groups[-1].strip()
        elif intent in ["create_file", "delete_file"] and groups:
            entities["target"] = groups[-1].strip()
        
        return entities
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities using predefined patterns"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches[0] if len(matches) == 1 else matches
        
        return entities


class ReasoningEngine:
    """Core reasoning engine with multi-factor decision making"""
    
    def __init__(self):
        self.confidence_weights = {
            "pattern_match": 0.4,
            "context_relevance": 0.2,
            "entity_extraction": 0.2,
            "historical_accuracy": 0.1,
            "user_preferences": 0.1
        }
        
    def calculate_confidence(self, factors: Dict[str, float]) -> float:
        """Calculate overall confidence using weighted factors"""
        total_confidence = 0.0
        total_weight = 0.0
        
        for factor, value in factors.items():
            if factor in self.confidence_weights:
                weight = self.confidence_weights[factor]
                total_confidence += value * weight
                total_weight += weight
        
        return min(1.0, total_confidence / total_weight if total_weight > 0 else 0.0)
    
    def build_reasoning_chain(self, text: str, intent: str, confidence: float, 
                            entities: Dict[str, Any], context_score: float) -> List[str]:
        """Build a reasoning chain explaining the decision process"""
        chain = []
        
        # Input analysis
        chain.append(f"Analyzed input: '{text}' ({len(text)} characters)")
        
        # Pattern matching
        if confidence > 0.7:
            chain.append(f"Strong pattern match for '{intent}' intent (confidence: {confidence:.2f})")
        elif confidence > 0.5:
            chain.append(f"Moderate pattern match for '{intent}' intent (confidence: {confidence:.2f})")
        else:
            chain.append(f"Weak pattern match for '{intent}' intent (confidence: {confidence:.2f})")
        
        # Entity extraction
        if entities:
            chain.append(f"Extracted entities: {list(entities.keys())}")
        else:
            chain.append("No specific entities identified")
        
        # Context analysis
        if context_score > 0.7:
            chain.append("Strong contextual relevance with conversation history")
        elif context_score > 0.3:
            chain.append("Moderate contextual relevance")
        else:
            chain.append("Low contextual relevance")
        
        # Decision rationale
        chain.append(f"Final decision: '{intent}' with {confidence:.1%} confidence")
        
        return chain
    
    def suggest_actions(self, intent: str, entities: Dict[str, Any], 
                       confidence: float) -> List[str]:
        """Suggest possible actions based on intent and confidence"""
        actions = []
        
        # High confidence actions
        if confidence > 0.8:
            actions.append(f"Execute {intent} immediately")
            
        # Medium confidence actions
        elif confidence > 0.5:
            actions.append(f"Execute {intent} with user confirmation")
            actions.append("Request clarification if needed")
            
        # Low confidence actions
        else:
            actions.append("Ask for clarification")
            actions.append("Provide alternative suggestions")
            actions.append("Show confidence level to user")
        
        # Intent-specific actions
        if intent == "unknown":
            actions.extend([
                "Show help menu",
                "Suggest common actions",
                "Enable learning mode"
            ])
        elif "application" in intent and entities.get("application"):
            actions.append(f"Target application: {entities['application']}")
        elif entities.get("file_name"):
            actions.append(f"Target file: {entities['file_name']}")
        
        return actions


class LearningAdapter:
    """Adaptive learning system for improving reasoning over time"""
    
    def __init__(self):
        self.interaction_history = []
        self.success_rates = defaultdict(list)
        self.pattern_adjustments = {}
        self.user_corrections = []
        
    def record_interaction(self, user_input: str, predicted_intent: str, 
                          confidence: float, actual_success: bool, 
                          user_feedback: Optional[str] = None):
        """Record interaction for learning"""
        interaction = {
            'timestamp': datetime.now(),
            'input': user_input,
            'predicted_intent': predicted_intent,
            'confidence': confidence,
            'success': actual_success,
            'feedback': user_feedback
        }
        
        self.interaction_history.append(interaction)
        self.success_rates[predicted_intent].append(actual_success)
        
        if user_feedback:
            self.user_corrections.append({
                'input': user_input,
                'predicted': predicted_intent,
                'corrected': user_feedback,
                'timestamp': datetime.now()
            })
    
    def get_historical_accuracy(self, intent: str) -> float:
        """Get historical accuracy for an intent"""
        if intent not in self.success_rates:
            return 0.5  # Default neutral score
        
        successes = self.success_rates[intent]
        if not successes:
            return 0.5
        
        # Weight recent interactions more heavily
        weighted_sum = 0.0
        total_weight = 0.0
        
        for i, success in enumerate(successes[-20:]):  # Last 20 interactions
            weight = 1.0 + (i * 0.1)  # More recent = higher weight
            weighted_sum += success * weight
            total_weight += weight
        
        return weighted_sum / total_weight
    
    def adapt_patterns(self) -> Dict[str, Any]:
        """Adapt patterns based on learning"""
        adaptations = {}
        
        # Analyze frequent failures
        for correction in self.user_corrections[-10:]:  # Recent corrections
            predicted = correction['predicted']
            corrected = correction['corrected']
            
            if predicted != corrected:
                adaptations[f"pattern_adjustment_{predicted}"] = {
                    'original_intent': predicted,
                    'suggested_intent': corrected,
                    'frequency': 1,
                    'confidence_adjustment': -0.1
                }
        
        return adaptations


class ReasoningManager:
    """Main reasoning manager coordinating all reasoning components"""
    
    def __init__(self, config_manager=None, logger=None):
        self.config_manager = config_manager
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize components
        self.context_manager = ContextManager()
        self.pattern_matcher = PatternMatcher()
        self.reasoning_engine = ReasoningEngine()
        self.learning_adapter = LearningAdapter()
        
        # Performance tracking
        self.processing_times = deque(maxlen=100)
        self.total_requests = 0
        self.successful_predictions = 0
        
    def classify_intent(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> IntentResult:
        """Main method to classify user intent with comprehensive reasoning"""
        start_time = time.time()
        
        try:
            # Preprocessing
            cleaned_input = self._preprocess_input(user_input)
            
            # Pattern matching
            intent, pattern_confidence, entities = self.pattern_matcher.match_intent(cleaned_input)
            
            # Context analysis
            context_score = self.context_manager.get_context_score(cleaned_input)
            
            # Historical accuracy
            historical_accuracy = self.learning_adapter.get_historical_accuracy(intent)
            
            # Calculate overall confidence
            confidence_factors = {
                "pattern_match": pattern_confidence,
                "context_relevance": context_score,
                "entity_extraction": min(1.0, len(entities) * 0.2),
                "historical_accuracy": historical_accuracy,
                "user_preferences": 0.5  # Placeholder - can be enhanced
            }
            
            final_confidence = self.reasoning_engine.calculate_confidence(confidence_factors)
            
            # Build reasoning chain
            reasoning_chain = self.reasoning_engine.build_reasoning_chain(
                cleaned_input, intent, final_confidence, entities, context_score
            )
            
            # Suggest actions
            suggested_actions = self.reasoning_engine.suggest_actions(
                intent, entities, final_confidence
            )
            
            # Determine category
            category = self._categorize_intent(intent)
            
            # Create result
            result = IntentResult(
                intent=intent,
                category=category,
                confidence=final_confidence,
                entities=entities,
                context_score=context_score,
                reasoning_chain=reasoning_chain,
                suggested_actions=suggested_actions,
                timestamp=datetime.now()
            )
            
            # Update context
            self.context_manager.add_interaction(user_input, result)
            
            # Performance tracking
            execution_time = time.time() - start_time
            self.processing_times.append(execution_time)
            self.total_requests += 1
            
            # Log result
            self.logger.info(f"Intent classified: {intent} (confidence: {final_confidence:.2f})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in intent classification: {e}", exc_info=True)
            return self._create_error_result(user_input, str(e))
    
    def log_reasoning_trace(self, user_input: str, result: IntentResult) -> ReasoningTrace:
        """Create and log detailed reasoning trace"""
        trace = ReasoningTrace(
            input_text=user_input,
            preprocessing_steps=[f"Cleaned input: {self._preprocess_input(user_input)}"],
            feature_extraction={
                "input_length": len(user_input),
                "word_count": len(user_input.split()),
                "has_entities": len(result.entities) > 0
            },
            classification_scores={result.intent: result.confidence},
            context_analysis={
                "context_score": result.context_score,
                "conversation_length": len(self.context_manager.conversation_history)
            },
            final_decision=result,
            execution_time=self.processing_times[-1] if self.processing_times else 0.0,
            confidence_factors={
                "final_confidence": result.confidence,
                "entity_count": len(result.entities)
            }
        )
        
        self.logger.debug(f"Reasoning trace: {asdict(trace)}")
        return trace
    
    def adapt_learning(self, user_input: str, predicted_intent: str, 
                      actual_outcome: bool, feedback: Optional[str] = None):
        """Adapt learning based on user feedback"""
        self.learning_adapter.record_interaction(
            user_input, predicted_intent, 0.0, actual_outcome, feedback
        )
        
        if actual_outcome:
            self.successful_predictions += 1
        
        adaptations = self.learning_adapter.adapt_patterns()
        if adaptations:
            self.logger.info(f"Learning adaptations made: {len(adaptations)} adjustments")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0.0
        success_rate = self.successful_predictions / self.total_requests if self.total_requests > 0 else 0.0
        
        return {
            "total_requests": self.total_requests,
            "successful_predictions": self.successful_predictions,
            "success_rate": success_rate,
            "average_processing_time": avg_processing_time,
            "recent_processing_times": list(self.processing_times)[-10:],
            "context_history_size": len(self.context_manager.conversation_history)
        }
    
    def _preprocess_input(self, text: str) -> str:
        """Preprocess user input for better matching"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Normalize contractions
        contractions = {
            "don't": "do not", "won't": "will not", "can't": "cannot",
            "shouldn't": "should not", "wouldn't": "would not"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        return text
    
    def _categorize_intent(self, intent: str) -> IntentCategory:
        """Categorize intent into broader categories"""
        category_mapping = {
            "shutdown_system": IntentCategory.SYSTEM_CONTROL,
            "restart_system": IntentCategory.SYSTEM_CONTROL,
            "sleep_system": IntentCategory.SYSTEM_CONTROL,
            "open_application": IntentCategory.APPLICATION,
            "close_application": IntentCategory.APPLICATION,
            "create_file": IntentCategory.FILE_MANAGEMENT,
            "delete_file": IntentCategory.FILE_MANAGEMENT,
            "search_files": IntentCategory.FILE_MANAGEMENT,
            "send_email": IntentCategory.COMMUNICATION,
            "make_call": IntentCategory.COMMUNICATION,
            "schedule_task": IntentCategory.AUTOMATION,
            "automate_process": IntentCategory.AUTOMATION,
            "get_weather": IntentCategory.QUERY,
            "get_time": IntentCategory.QUERY,
            "get_system_info": IntentCategory.SYSTEM_INFO,
            "set_reminder": IntentCategory.PERSONAL_ASSISTANT,
            "take_note": IntentCategory.PERSONAL_ASSISTANT,
        }
        
        return category_mapping.get(intent, IntentCategory.UNKNOWN)
    
    def _create_error_result(self, user_input: str, error: str) -> IntentResult:
        """Create error result when classification fails"""
        return IntentResult(
            intent="error",
            category=IntentCategory.UNKNOWN,
            confidence=0.0,
            entities={"error": error},
            context_score=0.0,
            reasoning_chain=[f"Error occurred: {error}"],
            suggested_actions=["Check input format", "Try rephrasing", "Contact support"],
            timestamp=datetime.now()
        )


# Example usage and testing functions
def test_reasoning_manager():
    """Test function for the reasoning manager"""
    rm = ReasoningManager()
    
    test_inputs = [
        "Open Chrome browser",
        "Shut down the computer",
        "Create a new document",
        "What's the weather like today?",
        "Set a reminder for 3 PM",
        "Delete the file report.pdf"
    ]
    
    print("Testing Reasoning Manager:")
    print("=" * 50)
    
    for test_input in test_inputs:
        result = rm.classify_intent(test_input)
        trace = rm.log_reasoning_trace(test_input, result)
        
        print(f"\nInput: {test_input}")
        print(f"Intent: {result.intent}")
        print(f"Category: {result.category.value}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Entities: {result.entities}")
        print(f"Suggested Actions: {result.suggested_actions[:2]}")  # Show first 2 actions
    
    print("\n" + "=" * 50)
    print("Performance Stats:")
    stats = rm.get_performance_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    test_reasoning_manager()
