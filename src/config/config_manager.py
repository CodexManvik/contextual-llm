"""
Configuration Manager for the Autonomous AI Assistant
Centralizes all configuration loading and provides easy access to config values
"""
import os
import json
import logging
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages all configuration for the AI assistant"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.configs = {}
        self.load_all_configs()
    
    def load_all_configs(self):
        """Load all configuration files"""
        self.load_env_config()
        self.load_settings_config()
        self.load_task_type_mapping()
        self.load_greeting_templates()
    
    def load_env_config(self):
        """Load environment variables with defaults"""
        self.configs['env'] = {
            # NVIDIA Configuration
            'NVIDIA_MODEL_PATH': os.getenv('NVIDIA_MODEL_PATH', 'models/prompt-task-and-complexity-classifier_vtask-llm-router'),
            'FALLBACK_THRESHOLD': float(os.getenv('FALLBACK_THRESHOLD', '0.6')),
            
            # LLM Configuration
            'OLLAMA_URL': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
            'OLLAMA_MODEL': os.getenv('OLLAMA_MODEL', 'gemma2:2b'),
            'LLM_TEMPERATURE': float(os.getenv('LLM_TEMPERATURE', '0.3')),
            
            # Voice Interface Configuration
            'SAMPLE_RATE': int(os.getenv('SAMPLE_RATE', '16000')),
            'VOICE_THRESHOLD': float(os.getenv('VOICE_THRESHOLD', '0.03')),
            
            # ASR Configuration
            'ASR_DEFAULT_SYSTEM': os.getenv('ASR_DEFAULT_SYSTEM', 'whisper'),
            'ASR_FALLBACK_SYSTEM': os.getenv('ASR_FALLBACK_SYSTEM', 'vosk'),
            'WHISPER_MODEL': os.getenv('WHISPER_MODEL', 'small'),
            'WHISPER_DEVICE': os.getenv('WHISPER_DEVICE', 'cpu'),
            'WHISPER_COMPUTE_TYPE': os.getenv('WHISPER_COMPUTE_TYPE', 'int8'),
            'WHISPER_LANGUAGE': os.getenv('WHISPER_LANGUAGE', 'en'),
            'WHISPER_BEAM_SIZE': int(os.getenv('WHISPER_BEAM_SIZE', '1')),
            'WHISPER_VAD_FILTER': os.getenv('WHISPER_VAD_FILTER', 'true').lower() == 'true',
            
            # User Preferences
            'USER_NAME': os.getenv('USER_NAME', 'User'),
            'ASSISTANT_NAME': os.getenv('ASSISTANT_NAME', 'AI Assistant'),
            'GREETING_STYLE': os.getenv('GREETING_STYLE', 'friendly'),
            'PRIVACY_LEVEL': os.getenv('PRIVACY_LEVEL', 'standard'),
            
            # Performance Settings
            'MAX_RESPONSE_TOKENS': int(os.getenv('MAX_RESPONSE_TOKENS', '300')),
            'BACKGROUND_TRAINING_ENABLED': os.getenv('BACKGROUND_TRAINING_ENABLED', 'false').lower() == 'true',
            'RESOURCE_MONITORING_ENABLED': os.getenv('RESOURCE_MONITORING_ENABLED', 'true').lower() == 'true',
            
            # Logging Configuration
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'LOG_FILE': os.getenv('LOG_FILE', 'logs/autonomous_assistant.log'),
            'LOG_ROTATION_SIZE': os.getenv('LOG_ROTATION_SIZE', '10MB'),
            'LOG_BACKUP_COUNT': int(os.getenv('LOG_BACKUP_COUNT', '5'))
        }
    
    def load_settings_config(self):
        """Load settings from JSON config file"""
        try:
            with open('config/settings.json', 'r') as f:
                self.configs['settings'] = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load settings.json: {e}")
            self.configs['settings'] = {}
    
    def load_task_type_mapping(self):
        """Load task type mapping from JSON config file"""
        try:
            with open('config/task_type_mapping.json', 'r') as f:
                self.configs['task_type_mapping'] = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load task_type_mapping.json: {e}")
            self.configs['task_type_mapping'] = {
                "0": "conversation",
                "1": "system_control",
                "2": "whatsapp_send",
                "3": "web_search",
                "4": "file_operation",
                "5": "keyboard_mouse",
                "6": "multi_step"
            }
    
    def load_greeting_templates(self):
        """Load greeting templates from JSON config file"""
        try:
            with open('config/greeting_templates.json', 'r') as f:
                self.configs['greeting_templates'] = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load greeting_templates.json: {e}")
            self.configs['greeting_templates'] = {
                "morning": "Good morning! I'm ready to help you with your tasks today.",
                "afternoon": "Good afternoon! How can I assist you?",
                "evening": "Good evening! I'm here to help with whatever you need.",
                "default": "Hello! I'm your AI assistant. How can I help you today?"
            }
    
    def get(self, key: str, default: Any = None, category: str = 'env') -> Any:
        """Get a configuration value"""
        category_config = self.configs.get(category, {})
        if not isinstance(category_config, dict):
            return default
        return category_config.get(key, default)
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """Get an environment configuration value"""
        return self.get(key, default, 'env')
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting from settings.json"""
        return self.get(key, default, 'settings')
    
    def get_task_type_mapping(self) -> Dict[str, str]:
        """Get the task type mapping"""
        return self.configs.get('task_type_mapping', {})
    
    def get_greeting_templates(self) -> Dict[str, str]:
        """Get the greeting templates"""
        return self.configs.get('greeting_templates', {})
    
    def update_setting(self, key: str, value: Any):
        """Update a setting and persist to file"""
        if 'settings' not in self.configs:
            self.configs['settings'] = {}
        
        self.configs['settings'][key] = value
        
        try:
            with open('config/settings.json', 'w') as f:
                json.dump(self.configs['settings'], f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to update settings.json: {e}")
