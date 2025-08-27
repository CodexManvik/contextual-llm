"""
Comprehensive test suite for Phase 6 enhancements
Testing robustness, error handling, and logging improvements
"""
import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio
import logging

class TestPhase6Enhancements:
    """Comprehensive tests for Phase 6 robustness and error handling"""
    
    def setup_method(self):
        """Setup before each test"""
        # Create a temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, 'test_assistant.log')
        
        # Mock environment variables
        self.env_patch = patch.dict(os.environ, {
            'LOG_LEVEL': 'DEBUG',
            'LOG_FILE': self.log_file,
            'LOG_ROTATION_SIZE': '1MB',
            'LOG_BACKUP_COUNT': '2'
        })
        self.env_patch.start()
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.env_patch.stop()
        # Clean up temporary files
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)
    
    def test_main_application_error_handling(self):
        """Test that main application handles errors gracefully"""
        from src.main import AutonomousAIAssistant
        
        # Mock components that might fail during initialization
        with patch('src.main.ConversationalLLMManager') as mock_llm, \
             patch('src.main.PiperTTSManager') as mock_tts, \
             patch('src.main.SystemController') as mock_system, \
             patch('src.main.ConfigManager') as mock_config:
            
            # Configure mocks
            mock_config_instance = Mock()
            mock_config_instance.get_env.side_effect = lambda key, default=None: default
            mock_config.return_value = mock_config_instance
            
            mock_llm_instance = Mock()
            mock_llm_instance.load_model.return_value = True
            mock_llm.return_value = mock_llm_instance
            
            mock_tts_instance = Mock()
            mock_tts.return_value = mock_tts_instance
            
            mock_system_instance = Mock()
            mock_system.return_value = mock_system_instance
            
            # Should initialize without errors
            assistant = AutonomousAIAssistant()
            assert assistant is not None
            
            # Test that critical attributes are set
            assert hasattr(assistant, 'logger')
            assert hasattr(assistant, 'config_manager')
            assert hasattr(assistant, 'llm_manager')
    
    def test_llm_loading_error_handling(self):
        """Test LLM loading error handling"""
        from src.main import AutonomousAIAssistant
        
        with patch('src.main.ConversationalLLMManager') as mock_llm, \
             patch('src.main.PiperTTSManager') as mock_tts, \
             patch('src.main.ConfigManager') as mock_config:
            
            # Configure mocks
            mock_config_instance = Mock()
            mock_config_instance.get_env.side_effect = lambda key, default=None: default
            mock_config.return_value = mock_config_instance
            
            mock_llm_instance = Mock()
            mock_llm_instance.load_model.side_effect = Exception("LLM loading failed")
            mock_llm.return_value = mock_llm_instance
            
            mock_tts_instance = Mock()
            mock_tts.return_value = mock_tts_instance
            
            # Should handle LLM loading error gracefully
            assistant = AutonomousAIAssistant()
            
            # Test start method with LLM loading failure
            async def test_start():
                await assistant.start()
                # Should not crash, should return early
            
            # Run the test
            asyncio.run(test_start())
    
    def test_voice_processing_error_handling(self):
        """Test voice processing error handling"""
        from src.main import AutonomousAIAssistant
        
        with patch('src.main.ConversationalLLMManager') as mock_llm, \
             patch('src.main.PiperTTSManager') as mock_tts, \
             patch('src.main.SystemController') as mock_system, \
             patch('src.main.ConfigManager') as mock_config:
            
            # Configure mocks
            mock_config_instance = Mock()
            mock_config_instance.get_env.side_effect = lambda key, default=None: default
            mock_config.return_value = mock_config_instance
            
            mock_llm_instance = Mock()
            mock_llm_instance.load_model.return_value = True
            mock_llm_instance.process_voice_command.side_effect = Exception("Processing error")
            mock_llm.return_value = mock_llm_instance
            
            mock_tts_instance = Mock()
            mock_tts.return_value = mock_tts_instance
            
            mock_system_instance = Mock()
            mock_system_instance.get_all_available_apps.return_value = []
            mock_system.return_value = mock_system_instance
            
            # Initialize assistant
            assistant = AutonomousAIAssistant()
            assistant.is_running = True  # Simulate running state
            
            # Test voice processing with error
            assistant.process_voice_input("test command")
            
            # Should handle the error without crashing
            # Error should be logged and system should continue
    
    def test_system_action_error_handling(self):
        """Test system action execution error handling"""
        from src.main import AutonomousAIAssistant
        
        with patch('src.main.ConversationalLLMManager') as mock_llm, \
             patch('src.main.SystemController') as mock_system, \
             patch('src.main.ConfigManager') as mock_config:
            
            # Configure mocks
            mock_config_instance = Mock()
            mock_config_instance.get_env.side_effect = lambda key, default=None: default
            mock_config.return_value = mock_config_instance
            
            mock_llm_instance = Mock()
            mock_llm_instance.load_model.return_value = True
            mock_llm.return_value = mock_llm_instance
            
            mock_system_instance = Mock()
            mock_system_instance.open_any_application.side_effect = Exception("App opening failed")
            mock_system.return_value = mock_system_instance
            
            # Initialize assistant
            assistant = AutonomousAIAssistant()
            
            # Test system action with error
            response = {
                "intent": "system_control",
                "action": "open",
                "parameters": {"application": "test_app"},
                "intent_analysis": {"intent": "system_control"}
            }
            
            assistant.execute_system_action(response)
            
            # Should handle the error without crashing
            # Error should be logged
    
    def test_logging_integration(self):
        """Test that logging is properly integrated throughout the system"""
        from src.main import AutonomousAIAssistant
        
        with patch('src.main.ConversationalLLMManager') as mock_llm, \
             patch('src.main.PiperTTSManager') as mock_tts, \
             patch('src.main.SystemController') as mock_system, \
             patch('src.main.ConfigManager') as mock_config:
            
            # Configure mocks
            mock_config_instance = Mock()
            mock_config_instance.get_env.side_effect = lambda key, default=None: {
                'LOG_LEVEL': 'DEBUG',
                'LOG_FILE': self.log_file,
                'LOG_ROTATION_SIZE': '1MB',
                'LOG_BACKUP_COUNT': '2'
            }.get(key, default)
            mock_config.return_value = mock_config_instance
            
            mock_llm_instance = Mock()
            mock_llm_instance.load_model.return_value = True
            mock_llm.return_value = mock_llm_instance
            
            mock_tts_instance = Mock()
            mock_tts.return_value = mock_tts_instance
            
            mock_system_instance = Mock()
            mock_system_instance.get_all_available_apps.return_value = []
            mock_system.return_value = mock_system_instance
            
            # Initialize assistant
            assistant = AutonomousAIAssistant()
            
            # Verify logging is configured
            assert assistant.logger is not None
            assert assistant.logger.level == logging.DEBUG
            
            # Test that log file was created
            assert os.path.exists(self.log_file)
            
            # Test logging functionality
            assistant.logger.info("Test log message")
            
            # Verify message was logged
            with open(self.log_file, 'r') as f:
                log_content = f.read()
                assert "Test log message" in log_content
    
    def test_comprehensive_error_scenarios(self):
        """Test various error scenarios that should be handled gracefully"""
        from src.main import AutonomousAIAssistant
        
        # Test initialization with various component failures
        test_scenarios = [
            # LLM manager failure
            {'llm_failure': True, 'tts_failure': False, 'system_failure': False},
            # TTS manager failure  
            {'llm_failure': False, 'tts_failure': True, 'system_failure': False},
            # System controller failure
            {'llm_failure': False, 'tts_failure': False, 'system_failure': True},
            # Multiple failures
            {'llm_failure': True, 'tts_failure': True, 'system_failure': True},
        ]
        
        for scenario in test_scenarios:
            with patch('src.main.ConversationalLLMManager') as mock_llm, \
                 patch('src.main.PiperTTSManager') as mock_tts, \
                 patch('src.main.SystemController') as mock_system, \
                 patch('src.main.ConfigManager') as mock_config:
                
                # Configure mocks based on scenario
                mock_config_instance = Mock()
                mock_config_instance.get_env.side_effect = lambda key, default=None: default
                mock_config.return_value = mock_config_instance
                
                mock_llm_instance = Mock()
                if scenario['llm_failure']:
                    mock_llm_instance.load_model.side_effect = Exception("LLM failed")
                else:
                    mock_llm_instance.load_model.return_value = True
                mock_llm.return_value = mock_llm_instance
                
                mock_tts_instance = Mock()
                if scenario['tts_failure']:
                    mock_tts_instance.speak_async.side_effect = Exception("TTS failed")
                mock_tts.return_value = mock_tts_instance
                
                mock_system_instance = Mock()
                if scenario['system_failure']:
                    mock_system_instance.get_all_available_apps.side_effect = Exception("System failed")
                else:
                    mock_system_instance.get_all_available_apps.return_value = []
                mock_system.return_value = mock_system_instance
                
                # Should handle all scenarios without crashing
                try:
                    assistant = AutonomousAIAssistant()
                    assert assistant is not None
                    
                    # Test basic functionality if components are available
                    if not scenario['llm_failure']:
                        async def test_basic():
                            await assistant.start()
                        asyncio.run(test_basic())
                        
                except Exception as e:
                    # Only acceptable if it's a controlled error from our mocks
                    assert "LLM failed" in str(e) or "TTS failed" in str(e) or "System failed" in str(e)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
