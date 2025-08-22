import logging
import numpy as np
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque, Counter
import threading
import time

class VoiceRecognitionOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Voice learning data
        self.recognition_data = {
            "corrections": deque(maxlen=200),  # Store recent corrections
            "confidence_scores": deque(maxlen=500),  # Store confidence tracking
            "environmental_profiles": {},  # Different environments (quiet, noisy, etc.)
            "user_vocabulary": set(),  # User's common words
            "phonetic_patterns": {},  # Sound pattern corrections
            "context_corrections": {}  # Context-based improvements
        }
        
        # Real-time optimization settings
        self.min_confidence_threshold = 0.7
        self.learning_enabled = True
        self.adaptation_strength = 0.3  # How aggressively to apply corrections
        
        # Background learning
        self._learning_thread = None
        self._stop_learning = False
        
        # Common speech recognition patterns
        self.common_corrections = {
            # App names
            "fire fox": "firefox",
            "mozilla firefox": "firefox",
            "google chrome": "chrome",
            "note pad": "notepad",
            "word pad": "wordpad",
            "calculator": "calc",
            "vs code": "vscode",
            "visual studio code": "vscode",
            
            # Commands
            "open up": "open",
            "start up": "start",
            "close down": "close",
            "shut down": "shutdown",
            
            # Common misrecognitions
            "firefox browser": "firefox",
            "chrome browser": "chrome",
            "word document": "word",
            "excel spreadsheet": "excel"
        }
        
        # Start background learning
        self._start_background_learning()
        
    def process_recognition_result(self, audio_data: bytes, recognized_text: str, 
                                 confidence: float, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process and optimize recognition result with AI enhancement"""
        
        original_text = recognized_text
        improved_text = recognized_text
        confidence_adjustments = []
        if context is None:
            context = {}
        # Apply learning-based improvements
        if self.learning_enabled:
            # Step 1: Apply learned corrections
            improved_text, correction_applied = self._apply_learned_corrections(improved_text)
            if correction_applied:
                confidence_adjustments.append(("learned_correction", 0.1))
            
            # Step 2: Apply context-based improvements
            if context:
                improved_text, context_applied = self._apply_context_improvements(improved_text, context)
                if context_applied:
                    confidence_adjustments.append(("context_improvement", 0.05))
            
            # Step 3: Apply common corrections
            improved_text, common_applied = self._apply_common_corrections(improved_text)
            if common_applied:
                confidence_adjustments.append(("common_correction", 0.05))
            
            # Step 4: Apply phonetic improvements
            improved_text, phonetic_applied = self._apply_phonetic_corrections(improved_text)
            if phonetic_applied:
                confidence_adjustments.append(("phonetic_correction", 0.08))
            
            # Collect data for learning
            self._collect_recognition_data(audio_data, original_text, improved_text, confidence, context)
        
        # Calculate improved confidence
        improved_confidence = self._calculate_improved_confidence(
            confidence, confidence_adjustments, improved_text
        )
        
        result = {
            "original_text": original_text,
            "improved_text": improved_text,
            "original_confidence": confidence,
            "improved_confidence": improved_confidence,
            "improvements_applied": improved_text != original_text,
            "confidence_adjustments": confidence_adjustments,
            "processing_time": time.time()
        }
        
        self.logger.debug(f"Voice optimization: '{original_text}' -> '{improved_text}' "
                         f"(confidence: {confidence:.3f} -> {improved_confidence:.3f})")
        
        return result
    
    def _apply_learned_corrections(self, text: str) -> Tuple[str, bool]:
        """Apply corrections learned from user feedback"""
        corrected = text.lower()
        applied = False
        
        # Apply recent corrections with highest priority
        for correction in list(self.recognition_data["corrections"])[-50:]:  # Most recent 50
            original = correction["original"].lower()
            fixed = correction["corrected"].lower()
            
            if original in corrected:
                corrected = corrected.replace(original, fixed)
                applied = True
                self.logger.debug(f"Applied learned correction: {original} -> {fixed}")
        
        return corrected, applied
    
    def _apply_context_improvements(self, text: str, context: Dict[str, Any]) -> Tuple[str, bool]:
        """Apply context-based improvements using available apps and recent commands"""
        improved = text.lower()
        applied = False
        
        # Get available apps from context
        available_apps = context.get("available_apps", [])
        recent_commands = context.get("system_state", {}).get("recent_commands", [])
        
        # Try to match against available apps
        words = improved.split()
        for i, word in enumerate(words):
            # Find closest app match
            best_match = self._find_closest_app_match(word, available_apps)
            if best_match and best_match != word:
                words[i] = best_match
                applied = True
                self.logger.debug(f"Context correction: {word} -> {best_match}")
        
        if applied:
            improved = " ".join(words)
        
        return improved, applied
    
    def _apply_common_corrections(self, text: str) -> Tuple[str, bool]:
        """Apply common speech recognition corrections"""
        corrected = text.lower()
        applied = False
        
        for wrong, correct in self.common_corrections.items():
            if wrong in corrected:
                corrected = corrected.replace(wrong, correct)
                applied = True
                self.logger.debug(f"Common correction: {wrong} -> {correct}")
        
        return corrected, applied
    
    def _apply_phonetic_corrections(self, text: str) -> Tuple[str, bool]:
        """Apply phonetic-based corrections for similar sounding words"""
        corrected = text.lower()
        applied = False
        
        # Phonetic corrections based on common misrecognitions
        phonetic_corrections = {
            # Similar sounding tech terms
            "fire fucks": "firefox",
            "fire folks": "firefox",
            "price talks": "firefox",  # Sometimes speech recognition gets creative
            "no pad": "notepad",
            "new pad": "notepad",
            "chrome book": "chrome",
            "home browser": "chrome",
            
            # Command corrections
            "pencil": "cancel",
            "opened": "open",
            "clothes": "close",
            "clothes that": "close that"
        }
        
        for wrong, correct in phonetic_corrections.items():
            if wrong in corrected:
                corrected = corrected.replace(wrong, correct)
                applied = True
                self.logger.debug(f"Phonetic correction: {wrong} -> {correct}")
        
        return corrected, applied
    
    def _find_closest_app_match(self, word: str, available_apps: List[str]) -> Optional[str]:
        """Find the closest matching app name"""
        if not available_apps:
            return None
        
        word_lower = word.lower()
        
        # Exact match first
        for app in available_apps:
            if word_lower == app.lower():
                return app.lower()
        
        # Substring match
        for app in available_apps:
            app_lower = app.lower()
            if word_lower in app_lower or app_lower in word_lower:
                return app_lower
        
        # Fuzzy match (simple similarity)
        best_match = None
        best_score = 0
        
        for app in available_apps:
            app_lower = app.lower()
            similarity = self._calculate_similarity(word_lower, app_lower)
            if similarity > 0.7 and similarity > best_score:
                best_score = similarity
                best_match = app_lower
        
        return best_match
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate simple string similarity"""
        if not str1 or not str2:
            return 0.0
        
        # Jaccard similarity based on character bigrams
        def get_bigrams(s):
            return set(s[i:i+2] for i in range(len(s)-1))
        
        bigrams1 = get_bigrams(str1)
        bigrams2 = get_bigrams(str2)
        
        if not bigrams1 and not bigrams2:
            return 1.0
        if not bigrams1 or not bigrams2:
            return 0.0
        
        intersection = len(bigrams1 & bigrams2)
        union = len(bigrams1 | bigrams2)
        
        return intersection / union
    
    def _calculate_improved_confidence(self, original_confidence: float, 
                                     adjustments: List[Tuple[str, float]], 
                                     improved_text: str) -> float:
        """Calculate improved confidence based on applied corrections"""
        
        confidence = original_confidence
        
        # Apply confidence boosts for corrections
        for adjustment_type, boost in adjustments:
            confidence += boost
        
        # Additional boosts
        # Boost for recognized vocabulary
        words = improved_text.lower().split()
        vocab_words = sum(1 for word in words if word in self.recognition_data["user_vocabulary"])
        if vocab_words > 0:
            vocab_boost = min(0.1, vocab_words * 0.02)
            confidence += vocab_boost
        
        # Boost for command patterns
        if any(cmd in improved_text.lower() for cmd in ["open", "close", "start", "launch"]):
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _collect_recognition_data(self, audio_data: bytes, original_text: str, 
                                improved_text: str, confidence: float, context: Dict[str, Any]):
        """Collect data for continuous learning"""
        
        # Store confidence information
        confidence_sample = {
            "original_text": original_text,
            "improved_text": improved_text,
            "confidence": confidence,
            "timestamp": datetime.now(),
            "audio_length": len(audio_data),
            "improvements_made": original_text != improved_text
        }
        
        self.recognition_data["confidence_scores"].append(confidence_sample)
        
        # Build user vocabulary from high-confidence recognitions
        if confidence > 0.8:
            words = improved_text.lower().split()
            self.recognition_data["user_vocabulary"].update(words)
        
        # Environmental profiling (basic)
        hour = datetime.now().hour
        env_key = f"hour_{hour}"
        if env_key not in self.recognition_data["environmental_profiles"]:
            self.recognition_data["environmental_profiles"][env_key] = {
                "samples": [],
                "avg_confidence": 0.0
            }
        
        env_profile = self.recognition_data["environmental_profiles"][env_key]
        env_profile["samples"].append(confidence)
        if len(env_profile["samples"]) > 50:
            env_profile["samples"] = env_profile["samples"][-50:]  # Keep recent
        
        env_profile["avg_confidence"] = np.mean(env_profile["samples"])
    
    def add_correction(self, original: str, corrected: str, context: Optional[Dict[str, Any]] = None):
        """Learn from user corrections with enhanced context"""
        correction = {
            "original": original.lower(),
            "corrected": corrected.lower(),
            "timestamp": datetime.now(),
            "context": context or {},
            "pattern_type": self._classify_correction_pattern(original, corrected),
            "confidence_boost": 0.15  # How much to boost confidence for this pattern
        }
        
        self.recognition_data["corrections"].append(correction)
        
        # Update context-specific corrections
        if context and "intent" in context:
            intent = context["intent"]
            if intent not in self.recognition_data["context_corrections"]:
                self.recognition_data["context_corrections"][intent] = []
            self.recognition_data["context_corrections"][intent].append(correction)
        
        # Update phonetic patterns
        self._update_phonetic_patterns(original, corrected)
        
        self.logger.info(f"Added correction: '{original}' -> '{corrected}' "
                        f"(pattern: {correction['pattern_type']})")
    
    def _classify_correction_pattern(self, original: str, corrected: str) -> str:
        """Classify the type of correction for better learning"""
        orig_words = original.lower().split()
        corr_words = corrected.lower().split()
        
        if len(orig_words) != len(corr_words):
            return "word_count_change"
        
        differences = sum(1 for o, c in zip(orig_words, corr_words) if o != c)
        
        if differences == 1:
            return "single_word_correction"
        elif differences <= len(orig_words) // 2:
            return "partial_correction"
        else:
            return "major_correction"
    
    def _update_phonetic_patterns(self, original: str, corrected: str):
        """Update phonetic pattern corrections"""
        # Simple phonetic pattern learning
        orig_sounds = self._extract_sound_patterns(original)
        corr_sounds = self._extract_sound_patterns(corrected)
        
        for orig_sound, corr_sound in zip(orig_sounds, corr_sounds):
            if orig_sound != corr_sound:
                if orig_sound not in self.recognition_data["phonetic_patterns"]:
                    self.recognition_data["phonetic_patterns"][orig_sound] = Counter()
                
                self.recognition_data["phonetic_patterns"][orig_sound][corr_sound] += 1
    
    def _extract_sound_patterns(self, text: str) -> List[str]:
        """Extract basic sound patterns from text"""
        # Simple approach: use syllable-like chunks
        text = re.sub(r'[^a-z ]', '', text.lower())
        words = text.split()
        
        patterns = []
        for word in words:
            # Split into vowel-consonant patterns
            pattern = ""
            for char in word:
                if char in "aeiou":
                    pattern += "V"
                elif char.isalpha():
                    pattern += "C"
            patterns.append(pattern)
        
        return patterns
    
    def _start_background_learning(self):
        """Start background learning thread"""
        if self._learning_thread is None:
            self._learning_thread = threading.Thread(target=self._background_learning_loop, daemon=True)
            self._learning_thread.start()
            self.logger.info("Started background voice learning")
    
    def _background_learning_loop(self):
        """Background learning loop for periodic optimization"""
        while not self._stop_learning:
            try:
                # Perform learning every 5 minutes
                time.sleep(300)
                
                if self.learning_enabled:
                    self._optimize_correction_patterns()
                    self._cleanup_old_data()
                    
            except Exception as e:
                self.logger.error(f"Background learning error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _optimize_correction_patterns(self):
        """Optimize correction patterns based on accumulated data"""
        # Find frequently corrected patterns
        pattern_counts = Counter()
        
        for correction in self.recognition_data["corrections"]:
            pattern_counts[correction["original"]] += 1
        
        # Update common corrections with frequent patterns
        for pattern, count in pattern_counts.most_common(10):
            if count >= 3:  # Pattern seen at least 3 times
                # Find the most common correction for this pattern
                corrections_for_pattern = [
                    c["corrected"] for c in self.recognition_data["corrections"]
                    if c["original"] == pattern
                ]
                
                if corrections_for_pattern:
                    most_common_correction = Counter(corrections_for_pattern).most_common(1)[0][0]
                    self.common_corrections[pattern] = most_common_correction
                    self.logger.info(f"Learned pattern: {pattern} -> {most_common_correction}")
    
    def _cleanup_old_data(self):
        """Clean up old learning data to prevent memory bloat"""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        # Clean old corrections
        recent_corrections = deque()
        for correction in self.recognition_data["corrections"]:
            if correction["timestamp"] > cutoff_date:
                recent_corrections.append(correction)
        
        self.recognition_data["corrections"] = recent_corrections
        
        # Clean old confidence scores
        recent_scores = deque()
        for score in self.recognition_data["confidence_scores"]:
            if score["timestamp"] > cutoff_date:
                recent_scores.append(score)
        
        self.recognition_data["confidence_scores"] = recent_scores
        
        self.logger.debug("Cleaned up old learning data")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about voice optimization"""
        corrections = list(self.recognition_data["corrections"])
        confidence_scores = list(self.recognition_data["confidence_scores"])
        
        # Calculate statistics
        avg_confidence = 0
        improvements_made = 0
        
        if confidence_scores:
            confidences = [s["confidence"] for s in confidence_scores]
            avg_confidence = np.mean(confidences)
            improvements_made = sum(1 for s in confidence_scores if s["improvements_made"])
        
        # Pattern analysis
        correction_patterns = Counter(c["pattern_type"] for c in corrections)
        
        # Environmental analysis
        env_stats = {}
        for env, data in self.recognition_data["environmental_profiles"].items():
            env_stats[env] = {
                "avg_confidence": data["avg_confidence"],
                "samples": len(data["samples"])
            }
        
        return {
            "vocabulary_size": len(self.recognition_data["user_vocabulary"]),
            "corrections_learned": len(corrections),
            "average_confidence": float(avg_confidence),
            "samples_collected": len(confidence_scores),
            "improvements_applied": improvements_made,
            "common_corrections": len(self.common_corrections),
            "phonetic_patterns": len(self.recognition_data["phonetic_patterns"]),
            "correction_patterns": dict(correction_patterns),
            "environmental_profiles": env_stats,
            "learning_enabled": self.learning_enabled
        }
    
    def stop_learning(self):
        """Stop background learning"""
        self._stop_learning = True
        if self._learning_thread:
            self._learning_thread.join(timeout=5)
        self.logger.info("Stopped background voice learning")
