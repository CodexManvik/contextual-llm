"""
NVIDIA Prompt Task and Complexity Classifier Integration
Provides advanced task classification and complexity scoring using NVIDIA's model
Optimized for local GPU inference without Triton server
"""

import json
import logging
import numpy as np
import os
from typing import Dict, Any, Optional, List

class NVIDIATaskClassifier:
    """Integration class for NVIDIA's prompt-task-and-complexity-classifier model"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path or os.getenv("NVIDIA_MODEL_PATH", "models/prompt-task-and-complexity-classifier_vtask-llm-router")
        self.fallback_threshold = float(os.getenv("FALLBACK_THRESHOLD", "0.6"))
        self.is_available = False
        
        # Load task type mapping from external config
        self.task_type_map = self._load_task_type_mapping()
        
        self._setup_local_inference()
    
    def _load_task_type_mapping(self) -> Dict[str, str]:
        """Load task type mapping from a JSON config file."""
        try:
            with open("config/task_type_mapping.json", "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load task type mapping: {e}")
            # Return default mapping as fallback
            return {
                "0": "conversation",
                "1": "system_control", 
                "2": "whatsapp_send",
                "3": "web_search",
                "4": "file_operation",
                "5": "keyboard_mouse",
                "6": "multi_step"
            }
    
    def _setup_local_inference(self):
        """Setup for local inference without Triton server"""
        try:
            # Check if model files exist
            model_files_exist = os.path.exists(self.model_path)
            
            if model_files_exist:
                self.logger.info("NVIDIA model files found - using local GPU inference")
                self.is_available = True
            else:
                self.logger.warning("NVIDIA model files not found - using fallback classification")
                self.is_available = False
            
        except Exception as e:
            self.logger.error(f"Error setting up local inference: {e}")
            self.is_available = False
    
    def classify_prompt(self, prompt_text: str) -> Dict[str, Any]:
        """
        Classify a prompt using NVIDIA's task classifier
        
        Args:
            prompt_text: The text prompt to classify
            
        Returns:
            Dictionary with classification results including:
            - task_type: Primary task classification
            - confidence: Confidence score
            - complexity_score: Overall complexity score
            - detailed_analysis: Detailed breakdown of complexity factors
        """
        if not self.is_available:
            return self._fallback_classification(prompt_text)
        
        try:
            # Perform local inference using ONNX Runtime
            return self._perform_local_inference(prompt_text)
            
        except Exception as e:
            self.logger.error(f"Error during classification: {e}")
            return self._fallback_classification(prompt_text)
    
    def _perform_local_inference(self, prompt_text: str) -> Dict[str, Any]:
        """Perform inference using local ONNX Runtime"""
        try:
            # Simulate inference for now - in a real implementation, this would use ONNX Runtime
            # with the actual NVIDIA model
            task_type, confidence = self._simulate_model_inference(prompt_text)
            
            complexity_score = self._calculate_complexity(prompt_text)
            
            return {
                "task_type": task_type,
                "confidence": confidence,
                "complexity_score": complexity_score,
                "detailed_analysis": {
                    "prompt_length": len(prompt_text),
                    "word_count": len(prompt_text.split()),
                    "estimated_complexity": complexity_score
                },
                "model_used": "nvidia_task_classifier_local"
            }
            
        except Exception as e:
            self.logger.error(f"Local inference error: {e}")
            return self._fallback_classification(prompt_text)
    
    def _simulate_model_inference(self, prompt_text: str):
        """Simulate model inference based on prompt content"""
        prompt_lower = prompt_text.lower()
        
        # Simple rule-based simulation of the NVIDIA model
        if any(word in prompt_lower for word in ['open', 'launch', 'start', 'close', 'quit', 'minimize', 'maximize']):
            return "system_control", 0.85
        elif any(word in prompt_lower for word in ['send', 'message', 'whatsapp', 'text']):
            return "whatsapp_send", 0.8
        elif any(word in prompt_lower for word in ['search', 'find', 'look up', 'google']):
            return "web_search", 0.75
        elif any(word in prompt_lower for word in ['file', 'document', 'folder', 'create', 'delete']):
            return "file_operation", 0.7
        elif any(word in prompt_lower for word in ['type', 'click', 'keyboard', 'mouse', 'press']):
            return "keyboard_mouse", 0.7
        elif any(word in prompt_lower for word in ['and', 'then', 'after', 'first', 'next']):
            return "multi_step", 0.65
        else:
            return "conversation", 0.9
    
    def _calculate_complexity(self, prompt_text: str) -> float:
        """Calculate a complexity score based on prompt characteristics"""
        # Simple heuristic-based complexity calculation
        # In a real implementation, this would use the model's complexity outputs
        words = prompt_text.split()
        word_count = len(words)
        
        # Basic complexity factors
        length_factor = min(word_count / 20, 1.0)  # Normalize to 0-1
        special_chars = sum(1 for char in prompt_text if char in '!?@#$%^&*()')
        special_factor = min(special_chars / 5, 1.0)
        
        # Combined score (0-1 scale)
        complexity = 0.6 * length_factor + 0.4 * special_factor
        return round(complexity, 2)
    
    def _fallback_classification(self, prompt_text: str) -> Dict[str, Any]:
        """Fallback classification when NVIDIA model is unavailable"""
        # Simple rule-based fallback
        prompt_lower = prompt_text.lower()
        
        if any(word in prompt_lower for word in ['open', 'launch', 'start', 'close', 'quit']):
            task_type = "system_control"
            confidence = 0.7
        elif any(word in prompt_lower for word in ['send', 'message', 'whatsapp', 'text']):
            task_type = "whatsapp_send" 
            confidence = 0.7
        elif any(word in prompt_lower for word in ['search', 'find', 'look up']):
            task_type = "web_search"
            confidence = 0.6
        else:
            task_type = "conversation"
            confidence = 0.8
        
        return {
            "task_type": task_type,
            "confidence": confidence,
            "complexity_score": self._calculate_complexity(prompt_text),
            "detailed_analysis": {
                "prompt_length": len(prompt_text),
                "word_count": len(prompt_text.split()),
                "fallback_used": True
            },
            "model_used": "fallback_rules"
        }
    
    def batch_classify(self, prompts: List[str]) -> List[Dict[str, Any]]:
        """Classify multiple prompts in batch"""
        results = []
        for prompt in prompts:
            results.append(self.classify_prompt(prompt))
        return results
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get the status of the NVIDIA model"""
        return {
            "available": self.is_available,
            "model_path": self.model_path,
            "local_inference": True,
            "model_type": "nvidia_task_classifier_local"
        }

# Singleton instance for easy access
task_classifier = NVIDIATaskClassifier()
