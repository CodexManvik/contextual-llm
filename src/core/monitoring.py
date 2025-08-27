"""
Monitoring and adaptation system for the Autonomous AI Assistant
Provides real-time monitoring of system states, resource usage, and background adaptation
"""
import os
import time
import threading
import logging
import psutil
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta

class SystemMonitor:
    """Monitors system states and resource usage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring_enabled = False
        self.monitoring_thread = None
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'processing_times': [],
            'active_listening': False,
            'is_processing': False,
            'last_command_time': None,
            'command_count': 0,
            'error_count': 0
        }
        
        # Thresholds for resource management
        self.cpu_threshold = 80.0  # %
        self.memory_threshold = 85.0  # %
        self.max_processing_time = 5.0  # seconds
        
    def start_monitoring(self):
        """Start background monitoring"""
        if self.monitoring_enabled:
            return
            
        self.monitoring_enabled = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("System monitoring started")
        
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_enabled = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        self.logger.info("System monitoring stopped")
        
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_enabled:
            try:
                self._collect_metrics()
                self._check_resource_usage()
                time.sleep(2.0)  # Collect metrics every 2 seconds
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(5.0)
                
    def _collect_metrics(self):
        """Collect system metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.metrics['cpu_usage'].append(cpu_percent)
        if len(self.metrics['cpu_usage']) > 60:  # Keep last minute of data
            self.metrics['cpu_usage'].pop(0)
            
        # Memory usage
        memory_percent = psutil.virtual_memory().percent
        self.metrics['memory_usage'].append(memory_percent)
        if len(self.metrics['memory_usage']) > 60:
            self.metrics['memory_usage'].pop(0)
            
    def _check_resource_usage(self):
        """Check if resource usage exceeds thresholds"""
        if self.metrics['cpu_usage']:
            avg_cpu = sum(self.metrics['cpu_usage']) / len(self.metrics['cpu_usage'])
            if avg_cpu > self.cpu_threshold:
                self.logger.warning(f"High CPU usage: {avg_cpu:.1f}%")
                
        if self.metrics['memory_usage']:
            avg_memory = sum(self.metrics['memory_usage']) / len(self.metrics['memory_usage'])
            if avg_memory > self.memory_threshold:
                self.logger.warning(f"High memory usage: {avg_memory:.1f}%")
                
    def update_processing_state(self, is_processing: bool):
        """Update processing state"""
        self.metrics['is_processing'] = is_processing
        if is_processing:
            self.metrics['last_command_time'] = datetime.now()
            
    def update_listening_state(self, is_listening: bool):
        """Update listening state"""
        self.metrics['active_listening'] = is_listening
        
    def record_command(self, processing_time: float):
        """Record command processing time"""
        self.metrics['processing_times'].append(processing_time)
        self.metrics['command_count'] += 1
        if len(self.metrics['processing_times']) > 100:  # Keep last 100 commands
            self.metrics['processing_times'].pop(0)
            
    def record_error(self):
        """Record error occurrence"""
        self.metrics['error_count'] += 1
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            'cpu_usage': self.metrics['cpu_usage'][-1] if self.metrics['cpu_usage'] else 0,
            'memory_usage': self.metrics['memory_usage'][-1] if self.metrics['memory_usage'] else 0,
            'active_listening': self.metrics['active_listening'],
            'is_processing': self.metrics['is_processing'],
            'command_count': self.metrics['command_count'],
            'error_count': self.metrics['error_count'],
            'avg_processing_time': sum(self.metrics['processing_times']) / len(self.metrics['processing_times']) 
                if self.metrics['processing_times'] else 0,
            'last_command_time': self.metrics['last_command_time']
        }
        
    def should_throttle(self) -> bool:
        """Determine if system should throttle processing"""
        if not self.metrics['cpu_usage'] or not self.metrics['memory_usage']:
            return False
            
        avg_cpu = sum(self.metrics['cpu_usage']) / len(self.metrics['cpu_usage'])
        avg_memory = sum(self.metrics['memory_usage']) / len(self.metrics['memory_usage'])
        
        return avg_cpu > self.cpu_threshold or avg_memory > self.memory_threshold


class BackgroundAdapter:
    """Handles background adaptation and learning"""
    
    def __init__(self, config_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.adaptation_enabled = False
        self.adaptation_thread = None
        self.learning_data = []
        self.last_adaptation = None
        
    def start_adaptation(self):
        """Start background adaptation"""
        if not self.config_manager.get_env('BACKGROUND_TRAINING_ENABLED', False):
            return
            
        self.adaptation_enabled = True
        self.adaptation_thread = threading.Thread(target=self._adaptation_loop, daemon=True)
        self.adaptation_thread.start()
        self.logger.info("Background adaptation started")
        
    def stop_adaptation(self):
        """Stop background adaptation"""
        self.adaptation_enabled = False
        if self.adaptation_thread:
            self.adaptation_thread.join(timeout=2.0)
        self.logger.info("Background adaptation stopped")
        
    def _adaptation_loop(self):
        """Background adaptation loop"""
        while self.adaptation_enabled:
            try:
                if self._should_adapt():
                    self._perform_adaptation()
                time.sleep(60.0)  # Check every minute
            except Exception as e:
                self.logger.error(f"Adaptation loop error: {e}")
                time.sleep(300.0)  # Wait 5 minutes on error
                
    def _should_adapt(self) -> bool:
        """Determine if adaptation should be performed"""
        # Adapt if we have sufficient learning data and it's been a while since last adaptation
        if len(self.learning_data) < 10:  # Minimum data points
            return False
            
        if self.last_adaptation and (datetime.now() - self.last_adaptation) < timedelta(hours=1):
            return False
            
        return True
        
    def _perform_adaptation(self):
        """Perform background adaptation"""
        self.logger.info("Performing background adaptation...")
        # Here you would implement actual adaptation logic
        # For example: fine-tuning models, updating patterns, etc.
        
        # Simulate adaptation work
        time.sleep(2.0)
        self.last_adaptation = datetime.now()
        self.logger.info("Background adaptation completed")
        
    def add_learning_data(self, data: Dict[str, Any]):
        """Add data for learning and adaptation"""
        self.learning_data.append(data)
        if len(self.learning_data) > 1000:  # Limit stored data
            self.learning_data.pop(0)
            
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            'data_points': len(self.learning_data),
            'last_adaptation': self.last_adaptation,
            'adaptation_enabled': self.adaptation_enabled
        }


class MonitoringManager:
    """Main monitoring manager that coordinates all monitoring activities"""
    
    def __init__(self, config_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.system_monitor = SystemMonitor()
        self.background_adapter = BackgroundAdapter(config_manager)
        
    def start_all_monitoring(self):
        """Start all monitoring and adaptation"""
        if self.config_manager.get_env('RESOURCE_MONITORING_ENABLED', True):
            self.system_monitor.start_monitoring()
            
        if self.config_manager.get_env('BACKGROUND_TRAINING_ENABLED', False):
            self.background_adapter.start_adaptation()
            
    def stop_all_monitoring(self):
        """Stop all monitoring and adaptation"""
        self.system_monitor.stop_monitoring()
        self.background_adapter.stop_adaptation()
        
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        system_metrics = self.system_monitor.get_metrics()
        learning_stats = self.background_adapter.get_learning_stats()
        
        return {
            'system': system_metrics,
            'learning': learning_stats,
            'monitoring_enabled': self.system_monitor.monitoring_enabled,
            'adaptation_enabled': self.background_adapter.adaptation_enabled,
            'timestamp': datetime.now()
        }
        
    def update_processing_state(self, is_processing: bool):
        """Update processing state"""
        self.system_monitor.update_processing_state(is_processing)
        
    def update_listening_state(self, is_listening: bool):
        """Update listening state"""
        self.system_monitor.update_listening_state(is_listening)
        
    def record_command(self, processing_time: float):
        """Record command processing"""
        self.system_monitor.record_command(processing_time)
        
    def record_error(self):
        """Record error"""
        self.system_monitor.record_error()
        
    def add_learning_data(self, data: Dict[str, Any]):
        """Add learning data"""
        self.background_adapter.add_learning_data(data)
        
    def should_throttle(self) -> bool:
        """Check if system should throttle processing"""
        return self.system_monitor.should_throttle()
