#!/usr/bin/env python3
"""
Comprehensive test for NVIDIA Task Classifier Integration
Tests all aspects including fallback mechanisms and edge cases
"""

import sys
import os
import logging
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NVIDIAIntegrationTester:
    """Comprehensive tester for NVIDIA integration"""
    
    def __init__(self):
        self.test_results = {
            'model_download': False,
            'dependencies': False,
            'config_setup': False,
            'classifier_init': False,
            'intent_parser': False,
            'fallback_mechanism': False,
            'edge_cases': False,
            'performance': False
        }
    
    def test_model_download(self):
        """Test if NVIDIA model files are present"""
        try:
            model_path = Path("models/prompt-task-and-complexity-classifier_vtask-llm-router")
            if model_path.exists():
                subdirs = [d for d in model_path.iterdir() if d.is_dir()]
                required_dirs = {'postprocessing_task_router', 'preprocessing_task_router', 
                                'task_router', 'task_router_ensemble'}
                present_dirs = {d.name for d in subdirs}
                
                if required_dirs.issubset(present_dirs):
                    logger.info(f"✅ Model files present: {present_dirs}")
                    self.test_results['model_download'] = True
                    return True
                else:
                    logger.warning(f"⚠️ Missing model directories. Present: {present_dirs}, Required: {required_dirs}")
            else:
                logger.error("❌ Model directory not found")
        except Exception as e:
            logger.error(f"❌ Model download test failed: {e}")
        return False
    
    def test_dependencies(self):
        """Test if required dependencies are installed"""
        try:
            import numpy as np
            import onnxruntime
            logger.info("✅ ONNX Runtime and numpy dependencies available")
            self.test_results['dependencies'] = True
            return True
        except ImportError as e:
            logger.error(f"❌ Dependency test failed: {e}")
            return False
    
    def test_config_setup(self):
        """Test if configuration is properly set up"""
        try:
            config_path = Path("config/settings.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                if 'nvidia_model' in config:
                    nvidia_config = config['nvidia_model']
                    if (nvidia_config.get('enabled', False) and 
                        nvidia_config.get('model_path')):
                        logger.info("✅ NVIDIA configuration properly set up")
                        self.test_results['config_setup'] = True
                        return True
                    else:
                        logger.warning("⚠️ NVIDIA configuration incomplete")
                else:
                    logger.error("❌ NVIDIA configuration missing from settings")
            else:
                logger.error("❌ Settings file not found")
        except Exception as e:
            logger.error(f"❌ Config test failed: {e}")
        return False
    
    def test_classifier_initialization(self):
        """Test NVIDIA classifier initialization"""
        try:
            from src.models.nvidia_task_classifier import NVIDIATaskClassifier
            
            classifier = NVIDIATaskClassifier()
            status = classifier.get_model_status()
            
            if 'status' in status:
                logger.info(f"✅ Classifier initialized successfully: {status}")
                self.test_results['classifier_init'] = True
                return True
            else:
                logger.warning("⚠️ Classifier initialization incomplete")
        except Exception as e:
            logger.error(f"❌ Classifier initialization test failed: {e}")
        return False
    
    def test_intent_parser_integration(self):
        """Test integration with intent parser"""
        try:
            from src.core.intent_parser import AdvancedIntentParser
            
            parser = AdvancedIntentParser()
            
            # Test basic commands
            test_commands = [
                "open notepad",
                "send message to john",
                "what time is it",
                "search for python tutorials"
            ]
            
            successful_parses = 0
            for cmd in test_commands:
                result = parser.parse_intent(cmd)
                if result and 'intent' in result:
                    successful_parses += 1
                    logger.info(f"   '{cmd}' -> {result['intent']}")
            
            if successful_parses >= len(test_commands) * 0.8:  # 80% success rate
                logger.info("✅ Intent parser integration working")
                self.test_results['intent_parser'] = True
                return True
            else:
                logger.warning(f"⚠️ Intent parser success rate: {successful_parses}/{len(test_commands)}")
        except Exception as e:
            logger.error(f"❌ Intent parser test failed: {e}")
        return False
    
    def test_fallback_mechanism(self):
        """Test fallback mechanism when NVIDIA model is unavailable"""
        try:
            from src.models.nvidia_task_classifier import NVIDIATaskClassifier
            
            classifier = NVIDIATaskClassifier()
            
            # Test prompts that should trigger fallback
            test_prompts = [
                "this is a simple conversation",
                "please open the browser",
                "can you help me with something"
            ]
            
            successful_fallbacks = 0
            for prompt in test_prompts:
                result = classifier.classify_prompt(prompt)
                if result and 'model_used' in result and 'fallback' in result['model_used'].lower():
                    successful_fallbacks += 1
                    logger.info(f"   '{prompt}' -> fallback used")
            
            if successful_fallbacks >= len(test_prompts) * 0.8:
                logger.info("✅ Fallback mechanism working correctly")
                self.test_results['fallback_mechanism'] = True
                return True
            else:
                logger.warning(f"⚠️ Fallback success rate: {successful_fallbacks}/{len(test_prompts)}")
        except Exception as e:
            logger.error(f"❌ Fallback test failed: {e}")
        return False
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        try:
            from src.models.nvidia_task_classifier import NVIDIATaskClassifier
            
            classifier = NVIDIATaskClassifier()
            
            edge_cases = [
                "",  # Empty string
                "   ",  # Whitespace only
                "a",  # Single character
                "this is a very long prompt that should test the limits of the classification system and ensure it handles longer inputs properly without crashing or timing out",  # Long prompt
                "!@#$%^&*()",  # Special characters
                "1234567890",  # Numbers only
            ]
            
            handled_cases = 0
            for case in edge_cases:
                try:
                    result = classifier.classify_prompt(case)
                    if result and 'task_type' in result:
                        handled_cases += 1
                        logger.info(f"   Edge case handled: '{case[:20]}...' -> {result['task_type']}")
                except Exception:
                    logger.warning(f"   Edge case failed: '{case[:20]}...'")
            
            if handled_cases >= len(edge_cases) * 0.7:  # 70% success rate for edge cases
                logger.info("✅ Edge case handling working")
                self.test_results['edge_cases'] = True
                return True
            else:
                logger.warning(f"⚠️ Edge case success rate: {handled_cases}/{len(edge_cases)}")
        except Exception as e:
            logger.error(f"❌ Edge case test failed: {e}")
        return False
    
    def test_performance(self):
        """Test performance characteristics"""
        try:
            from src.models.nvidia_task_classifier import NVIDIATaskClassifier
            import time
            
            classifier = NVIDIATaskClassifier()
            
            # Test response time
            test_prompt = "open chrome browser please"
            start_time = time.time()
            
            for _ in range(5):  # Multiple runs for average
                result = classifier.classify_prompt(test_prompt)
            
            end_time = time.time()
            avg_time = (end_time - start_time) / 5
            
            if avg_time < 2.0:  # Reasonable response time
                logger.info(f"✅ Performance acceptable: {avg_time:.3f}s average response time")
                self.test_results['performance'] = True
                return True
            else:
                logger.warning(f"⚠️ Performance slow: {avg_time:.3f}s average response time")
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
        return False
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        logger.info("🚀 Starting Comprehensive NVIDIA Integration Tests")
        logger.info("=" * 60)
        
        tests = [
            ("Model Download", self.test_model_download),
            ("Dependencies", self.test_dependencies),
            ("Config Setup", self.test_config_setup),
            ("Classifier Init", self.test_classifier_initialization),
            ("Intent Parser", self.test_intent_parser_integration),
            ("Fallback Mechanism", self.test_fallback_mechanism),
            ("Edge Cases", self.test_edge_cases),
            ("Performance", self.test_performance),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Testing: {test_name}")
            test_func()
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} {test_name.replace('_', ' ').title()}")
        
        logger.info("=" * 60)
        logger.info(f"Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests >= total_tests * 0.7:
            logger.info("🎉 NVIDIA Integration is working correctly!")
            return True
        else:
            logger.warning("⚠️ NVIDIA Integration needs attention")
            return False

def main():
    """Main test function"""
    tester = NVIDIAIntegrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
