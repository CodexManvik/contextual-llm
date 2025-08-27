"""
Logging Utilities for the Autonomous AI Assistant
Enhanced logging with rotation, formatting, centralized configuration, and monitoring
"""
import os
import json
import time
import uuid
import logging
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from typing import Optional, Dict, Any, Union
from pathlib import Path
from contextvars import ContextVar
from functools import wraps
from queue import Queue
import threading


# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default=None)
user_id_var: ContextVar[str] = ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add context variables if present
        request_id = request_id_var.get()
        if request_id:
            log_data['request_id'] = request_id
            
        user_id = user_id_var.get()
        if user_id:
            log_data['user_id'] = user_id
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'exc_info', 'exc_text', 'stack_info']:
                log_data[key] = value
                
        return json.dumps(log_data, default=str)


class ContextFormatter(logging.Formatter):
    """Standard formatter that includes context variables"""
    
    def format(self, record):
        # Add context to record
        request_id = request_id_var.get()
        if request_id:
            record.request_id = request_id
            
        user_id = user_id_var.get()
        if user_id:
            record.user_id = user_id
            
        return super().format(record)


class LoggingManager:
    """Manages logging configuration and rotation for the entire system"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.loggers = {}
        self.setup_complete = False
        self.queue_listener = None
        self._lock = threading.Lock()
    
    def setup_logging(self):
        """Setup comprehensive logging system with rotation"""
        with self._lock:
            if self.setup_complete:
                return
                
            try:
                self._configure_logging()
                self.setup_complete = True
                root_logger = logging.getLogger()
                root_logger.info("Logging system initialized successfully")
            except Exception as e:
                print(f"Failed to setup logging: {e}")
                self._setup_fallback_logging()
    
    def _configure_logging(self):
        """Internal method to configure logging"""
        # Get and validate configuration
        log_level = self._validate_log_level(
            self.config_manager.get_env('LOG_LEVEL', 'INFO')
        )
        log_file = self.config_manager.get_env('LOG_FILE', 'logs/autonomous_assistant.log')
        rotation_size = self.config_manager.get_env('LOG_ROTATION_SIZE', '10MB')
        backup_count = int(self.config_manager.get_env('LOG_BACKUP_COUNT', 5))
        use_json = self.config_manager.get_env('LOG_JSON_FORMAT', False)
        enable_async = self.config_manager.get_env('LOG_ASYNC', False)
        
        # Parse rotation size
        max_bytes = self._parse_size_string(rotation_size)
        
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create formatters
        if use_json:
            formatter = StructuredFormatter(datefmt='%Y-%m-%d %H:%M:%S')
            console_formatter = ContextFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            format_string = '%(asctime)s - %(name)s - %(levelname)s'
            
            # Add context to format if available
            request_id = request_id_var.get()
            if request_id:
                format_string += ' - [%(request_id)s]'
                
            format_string += ' - %(message)s'
            
            formatter = ContextFormatter(format_string, datefmt='%Y-%m-%d %H:%M:%S')
            console_formatter = formatter
        
        if enable_async:
            # Setup async logging with queue
            log_queue = Queue(-1)  # No size limit
            
            # File handler for queue
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            
            # Console handler for queue
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(console_formatter)
            
            # Queue listener
            self.queue_listener = QueueListener(
                log_queue, file_handler, console_handler, respect_handler_level=True
            )
            self.queue_listener.start()
            
            # Queue handler for root logger
            queue_handler = QueueHandler(log_queue)
            root_logger.addHandler(queue_handler)
        else:
            # Synchronous logging
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Configure per-module log levels
        self._configure_module_levels()
    
    def _setup_fallback_logging(self):
        """Setup minimal console logging as fallback"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        self.setup_complete = True
        root_logger.warning("Using fallback logging configuration")
    
    def _validate_log_level(self, level: str) -> str:
        """Validate and return log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        level = level.upper()
        if level not in valid_levels:
            print(f"Invalid LOG_LEVEL '{level}', defaulting to INFO")
            return 'INFO'
        return level
    
    def _configure_module_levels(self):
        """Configure per-module log levels"""
        try:
            module_levels = self.config_manager.get_env('MODULE_LOG_LEVELS', {})
            for module_name, level in module_levels.items():
                module_logger = logging.getLogger(module_name)
                validated_level = self._validate_log_level(level)
                module_logger.setLevel(getattr(logging, validated_level))
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to configure module levels: {e}")
    
    def _parse_size_string(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes"""
        size_str = size_str.upper().strip()
        multipliers = {
            'GB': 1024 * 1024 * 1024,
            'MB': 1024 * 1024,
            'KB': 1024,
            'B': 1
        }
        
        for unit, multiplier in multipliers.items():
            if size_str.endswith(unit):
                try:
                    num = float(size_str[:-len(unit)])
                    return int(num * multiplier)
                except ValueError:
                    break
        
        # Default to 10MB if parsing fails
        print(f"Invalid size format '{size_str}', defaulting to 10MB")
        return 10 * 1024 * 1024
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a named logger with proper configuration"""
        if not self.setup_complete:
            self.setup_logging()
        
        # Check if we've already configured this logger
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        # Named loggers inherit from root logger, so no additional configuration needed
        self.loggers[name] = logger
        return logger
    
    def rotate_logs(self):
        """Manually rotate log files"""
        root_logger = logging.getLogger()
        rotated_count = 0
        
        for handler in root_logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                handler.doRollover()
                rotated_count += 1
        
        root_logger.info(f"Rotated {rotated_count} log file(s) manually")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get statistics about logging configuration"""
        root_logger = logging.getLogger()
        stats = {
            'log_level': logging.getLevelName(root_logger.level),
            'handlers_count': len(root_logger.handlers),
            'handlers': [],
            'loggers_count': len(logging.Logger.manager.loggerDict),
            'async_enabled': self.queue_listener is not None
        }
        
        for handler in root_logger.handlers:
            handler_info = {
                'type': handler.__class__.__name__,
                'level': logging.getLevelName(handler.level)
            }
            
            if isinstance(handler, RotatingFileHandler):
                handler_info.update({
                    'filename': handler.baseFilename,
                    'max_bytes': handler.maxBytes,
                    'backup_count': handler.backupCount,
                    'current_size': os.path.getsize(handler.baseFilename) 
                                  if os.path.exists(handler.baseFilename) else 0
                })
            
            stats['handlers'].append(handler_info)
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Check logging system health"""
        health = {
            'status': 'healthy',
            'issues': [],
            'log_file_exists': False,
            'log_file_writable': False,
            'handlers_active': 0,
            'setup_complete': self.setup_complete
        }
        
        if not self.setup_complete:
            health['status'] = 'unhealthy'
            health['issues'].append('Logging not initialized')
            return health
        
        root_logger = logging.getLogger()
        active_handlers = [h for h in root_logger.handlers if h]
        health['handlers_active'] = len(active_handlers)
        
        # Check file handlers
        for handler in root_logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                log_file = handler.baseFilename
                health['log_file_exists'] = os.path.exists(log_file)
                
                try:
                    # Test write access
                    with open(log_file, 'a', encoding='utf-8'):
                        pass
                    health['log_file_writable'] = True
                except (OSError, IOError) as e:
                    health['log_file_writable'] = False
                    health['issues'].append(f'Log file not writable: {e}')
                    health['status'] = 'degraded'
        
        if health['handlers_active'] == 0:
            health['issues'].append('No active log handlers')
            health['status'] = 'unhealthy'
        
        return health
    
    def shutdown(self):
        """Shutdown logging system gracefully"""
        if self.queue_listener:
            self.queue_listener.stop()
            self.queue_listener = None
        
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)
        
        self.setup_complete = False
        logging.shutdown()


class RequestContext:
    """Context manager for request-scoped logging"""
    
    def __init__(self, request_id: str = None, user_id: str = None):
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
        self.request_token = None
        self.user_token = None
    
    def __enter__(self):
        self.request_token = request_id_var.set(self.request_id)
        if self.user_id:
            self.user_token = user_id_var.set(self.user_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.request_token:
            request_id_var.reset(self.request_token)
        if self.user_token:
            user_id_var.reset(self.user_token)


def log_performance(logger_name: str = None, log_args: bool = False):
    """Decorator to log function execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            start_time = time.time()
            
            # Log function entry
            if log_args:
                logger.debug(f"Entering {func.__name__} with args={args}, kwargs={kwargs}")
            else:
                logger.debug(f"Entering {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{func.__name__} completed in {execution_time:.4f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.4f}s: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


def setup_global_logging(config_manager):
    """Setup global logging configuration"""
    global _logging_manager
    _logging_manager = LoggingManager(config_manager)
    _logging_manager.setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Get a logger with global configuration"""
    global _logging_manager
    if _logging_manager is None:
        # Create a basic fallback logger with console handler
        logger = logging.getLogger(name)
        if not logger.handlers and not logger.parent.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.warning("Using fallback logger - global logging not configured")
        return logger
    return _logging_manager.get_logger(name)


def rotate_logs():
    """Rotate log files globally"""
    global _logging_manager
    if _logging_manager:
        _logging_manager.rotate_logs()
    else:
        logging.getLogger(__name__).warning("Cannot rotate logs - logging manager not initialized")


def get_logging_stats() -> Dict[str, Any]:
    """Get global logging statistics"""
    global _logging_manager
    if _logging_manager:
        return _logging_manager.get_log_stats()
    return {'error': 'Logging manager not initialized'}


def get_logging_health() -> Dict[str, Any]:
    """Get global logging health status"""
    global _logging_manager
    if _logging_manager:
        return _logging_manager.health_check()
    return {'status': 'unhealthy', 'issues': ['Logging manager not initialized']}


def shutdown_logging():
    """Shutdown global logging system"""
    global _logging_manager
    if _logging_manager:
        _logging_manager.shutdown()
        _logging_manager = None


# Convenience context manager
def request_context(request_id: str = None, user_id: str = None):
    """Create a request context for logging"""
    return RequestContext(request_id, user_id)


# Example usage functions for testing
def test_logging():
    """Test function to demonstrate logging capabilities"""
    logger = get_logger(__name__)
    
    with request_context(user_id="test_user") as ctx:
        logger.info("Testing logging with context")
        logger.debug("Debug message with context")
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.error("Caught test exception", exc_info=True)


@log_performance(__name__)
def example_function(delay: float = 1.0):
    """Example function to demonstrate performance logging"""
    time.sleep(delay)
    return f"Completed after {delay}s"


if __name__ == "__main__":
    # Example configuration for testing
    class MockConfig:
        def get_env(self, key: str, default=None):
            config = {
                'LOG_LEVEL': 'DEBUG',
                'LOG_FILE': 'logs/test.log',
                'LOG_JSON_FORMAT': False,
                'LOG_ASYNC': True
            }
            return config.get(key, default)
    
    # Initialize logging
    setup_global_logging(MockConfig())
    
    # Test the logging system
    test_logging()
    example_function(0.5)
    
    # Print statistics
    print("Logging Stats:", get_logging_stats())
    print("Health Check:", get_logging_health())
    
    # Cleanup
    shutdown_logging()
