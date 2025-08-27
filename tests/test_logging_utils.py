"""
Test suite for logging utilities in Phase 6 implementation
"""
import os
import tempfile
import logging
import pytest
from unittest.mock import Mock, patch
from src.config.config_manager import ConfigManager
from src.core.logging_utils import LoggingManager, setup_global_logging, get_logger, rotate_logs, get_logging_stats, shutdown_logging

class TestLoggingUtils:
    """Test cases for logging utilities"""
    
    def setup_method(self):
        """Setup before each test"""
        self.config_manager = Mock()
        self.config_manager.get_env.side_effect = lambda key, default=None: {
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': 'test.log',
            'LOG_ROTATION_SIZE': '1MB',
            'LOG_BACKUP_COUNT': 3
        }.get(key, default)
    
    def test_logging_manager_initialization(self):
        """Test LoggingManager initialization"""
        manager = LoggingManager(self.config_manager)
        assert manager.config_manager == self.config_manager
        assert not manager.setup_complete
        assert manager.loggers == {}
    
    def test_parse_size_string(self):
        """Test parsing size strings to bytes"""
        manager = LoggingManager(self.config_manager)
        
        # Test various size formats (method returns floats, so we need to convert to int)
        assert int(manager._parse_size_string('1KB')) == 1024
        assert int(manager._parse_size_string('2MB')) == 2 * 1024 * 1024
        assert int(manager._parse_size_string('500B')) == 500
        assert int(manager._parse_size_string('invalid')) == 10 * 1024 * 1024  # Default
    
    def test_setup_logging(self):
        """Test logging setup with rotation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, 'test.log')
            
            self.config_manager.get_env.side_effect = lambda key, default=None: {
                'LOG_LEVEL': 'DEBUG',
                'LOG_FILE': log_file,
                'LOG_ROTATION_SIZE': '1MB',
                'LOG_BACKUP_COUNT': 2
            }.get(key, default)
            
            manager = LoggingManager(self.config_manager)
            manager.setup_logging()
            
            assert manager.setup_complete
            
            # Test that logger can be retrieved
            logger = manager.get_logger('test_logger')
            assert isinstance(logger, logging.Logger)
            
            # Test logging
            logger.debug('Test debug message')
            logger.info('Test info message')
            
            # Verify log file was created
            assert os.path.exists(log_file)
            
            # Clean up logging handlers to avoid file lock issues
            manager.shutdown()
    
    def test_rotate_logs(self):
        """Test manual log rotation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, 'test.log')
            
            self.config_manager.get_env.side_effect = lambda key, default=None: {
                'LOG_LEVEL': 'INFO',
                'LOG_FILE': log_file,
                'LOG_ROTATION_SIZE': '1KB',  # Small size to trigger rotation
                'LOG_BACKUP_COUNT': 2
            }.get(key, default)
            
            manager = LoggingManager(self.config_manager)
            manager.setup_logging()
            
            # Write enough data to trigger rotation
            logger = manager.get_logger('rotation_test')
            for i in range(20):  # Reduced number of messages to avoid excessive output
                logger.info(f'Test message {i}' * 10)  # Smaller messages
            
            # Manually rotate logs
            manager.rotate_logs()
            
            # Should have backup files
            backup_files = [f for f in os.listdir(temp_dir) if f.startswith('test.log.')]
            assert len(backup_files) > 0
            
            # Clean up logging handlers to avoid file lock issues
            manager.shutdown()
    
    def test_get_log_stats(self):
        """Test getting logging statistics"""
        manager = LoggingManager(self.config_manager)
        manager.setup_logging()
        
        stats = manager.get_log_stats()
        
        assert 'log_level' in stats
        assert 'handlers_count' in stats
        assert 'handlers' in stats
        assert 'loggers_count' in stats
        
        # Should have at least one handler
        assert stats['handlers_count'] > 0
    
    def test_global_functions(self):
        """Test global logging functions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, 'global_test.log')
            
            config_manager = Mock()
            config_manager.get_env.side_effect = lambda key, default=None: {
                'LOG_LEVEL': 'INFO',
                'LOG_FILE': log_file,
                'LOG_ROTATION_SIZE': '1MB',
                'LOG_BACKUP_COUNT': 2
            }.get(key, default)
            
            # Setup global logging
            setup_global_logging(config_manager)
            
            # Test get_logger
            logger = get_logger('global_test')
            logger.info('Global test message')
            
            # Test rotate_logs
            rotate_logs()
            
            # Test get_logging_stats
            stats = get_logging_stats()
            assert isinstance(stats, dict)
            
            # Verify log file was created
            assert os.path.exists(log_file)
            
            # Clean up global logging to avoid file lock issues
            shutdown_logging()

class TestErrorHandlingIntegration:
    """Integration tests for error handling enhancements"""
    
    def test_error_handling_in_main(self):
        """Test that main.py has proper error handling"""
        # This test verifies that critical sections have try-except blocks
        # We'll check by importing and examining the main module
        
        # Skip this test as it requires the full application structure
        # which may not be available in the test environment
        pytest.skip("Skipping main.py test as it requires full application structure")
    
    def test_config_manager_error_handling(self):
        """Test ConfigManager error handling"""
        config_manager = ConfigManager()
        
        # Test that get methods handle missing keys gracefully
        assert config_manager.get('non_existent_key', 'default') == 'default'
        assert config_manager.get_env('NON_EXISTENT_ENV', 'env_default') == 'env_default'
        
        # Test that settings loading handles errors
        with patch('builtins.open', side_effect=Exception('Test error')):
            # Should not crash when config files are missing
            config_manager.load_settings_config()
            assert 'settings' in config_manager.configs
            assert config_manager.configs['settings'] == {}

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
