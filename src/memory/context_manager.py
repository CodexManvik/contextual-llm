# Advanced Context Manager
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Dict, List, Any

class FileSystemWatcher(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
    
    def on_modified(self, event):
        self.callback(event.src_path, "modified")

class AdvancedContextManager:
    def __init__(self):
        self.file_observer = Observer()
        self.file_observer.schedule(FileSystemWatcher(self._handle_file_change), path='.', recursive=True)
        self.file_observer.start()
        self.recent_changes: List[str] = []
    
    def _handle_file_change(self, path: str, change_type: str):
        self.recent_changes.append(f"{change_type}: {path}")
        if len(self.recent_changes) > 50:
            self.recent_changes = self.recent_changes[-50:]
    
    def get_active_apps(self) -> List[str]:
        """Get currently running applications"""
        return [p.info['name'] for p in psutil.process_iter(['name']) if p.info['name']]
    
    def get_current_context(self) -> Dict[str, Any]:
        """Gather current system context"""
        return {
            "active_apps": self.get_active_apps(),
            "recent_files": self.recent_changes,
            "system_stats": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent
            }
        }
    
    def __del__(self):
        self.file_observer.stop()
        self.file_observer.join()
