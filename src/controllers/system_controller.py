# Enhanced System Controller with Tool Execution
import pyautogui
import pywinauto
import subprocess
import os
import psutil
import logging
import webbrowser
from typing import Dict, List, Optional, Any
from .app_discovery import discover_installed_apps, resolve_app

class AdvancedSystemController:
    def __init__(self):
        pyautogui.PAUSE = 0.3
        pyautogui.FAILSAFE = True
        self.logger = logging.getLogger(__name__)
        
        # Dynamic app registry - updated in real-time
        self.refresh_app_registry()
    
    def refresh_app_registry(self) -> int:
        """Refresh the dynamic app registry"""
        self._app_registry = discover_installed_apps(rescan=True)
        self.logger.info(f"Discovered {len(self._app_registry)} applications")
        return len(self._app_registry)
    
    def get_all_available_apps(self) -> List[str]:
        """Get list of all discoverable applications"""
        return [app['app_name'] for app in self._app_registry]
    
    def open_any_application(self, app_name: str) -> Dict[str, Any]:
        """Open any application dynamically"""
        app = resolve_app(app_name, self._app_registry)
        
        if app:
            try:
                os.startfile(app['main_exe'])
                return {
                    "success": True,
                    "message": f"Opened {app['app_name']}",
                    "app_info": app
                }
            except Exception as e:
                self.logger.error(f"Failed to open {app['app_name']}: {e}")
        
        # Fallback: try system command
        try:
            subprocess.Popen(app_name, shell=True)
            return {
                "success": True,
                "message": f"Opened {app_name} via system command",
                "app_info": {"app_name": app_name}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Could not open {app_name}: {str(e)}",
                "app_info": None
            }
    
    def web_search(self, query: str) -> bool:
        """Perform web search"""
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return True
        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return False
    
    def keyboard_action(self, action_type: str, **kwargs) -> bool:
        """Perform keyboard actions"""
        try:
            if action_type == "type":
                text = kwargs.get("text", "")
                pyautogui.write(text)
            elif action_type == "hotkey":
                keys = kwargs.get("keys", "").split('+')
                pyautogui.hotkey(*keys)
            elif action_type == "key":
                key = kwargs.get("key", "")
                pyautogui.press(key)
            
            return True
        except Exception as e:
            self.logger.error(f"Keyboard action failed: {e}")
            return False
    
    def mouse_action(self, action_type: str, **kwargs) -> bool:
        """Perform mouse actions"""
        try:
            if action_type == "click":
                x = kwargs.get("x")
                y = kwargs.get("y")
                if x and y:
                    pyautogui.click(x, y)
                else:
                    pyautogui.click()
            elif action_type == "scroll":
                scrolls = kwargs.get("scrolls", 3)
                pyautogui.scroll(scrolls)
            
            return True
        except Exception as e:
            self.logger.error(f"Mouse action failed: {e}")
            return False
    
    def file_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Perform file operations"""
        try:
            if operation == "create_folder":
                path = kwargs.get("path", "")
                os.makedirs(path, exist_ok=True)
                return {"success": True, "message": f"Created folder: {path}"}
            
            elif operation == "open_file":
                path = kwargs.get("path", "")
                os.startfile(path)
                return {"success": True, "message": f"Opened: {path}"}
            
            # Add more file operations as needed

            # If no operation matched, return a failure message
            return {"success": False, "message": f"Unknown file operation: {operation}"}
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def execute_with_confirmation(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute actions with confirmation for safety"""
        # Show preview
        preview = self.dry_run_action(action, **kwargs)
        
        # Get user confirmation (implement voice/text confirmation as needed)
        confirmed = True  # Placeholder - add real confirmation logic
        
        if confirmed:
            result = self.execute_action(action, **kwargs)
            self.logger.info(f"Action executed: {action}")
            return result
        else:
            return {"success": False, "message": "Action cancelled by user"}
    
    def dry_run_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """Simulate action without executing"""
        # Implement dry-run logic for each action type
        return {"preview": f"Would perform {action} with params {kwargs}"}
    
    def execute_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """Core action executor"""
        # Route to appropriate method
        if action == "open_app":
            return self.open_any_application(kwargs.get("app_name", ""))
        elif action == "web_search":
            return {"success": self.web_search(kwargs.get("query", ""))}
        elif action == "keyboard":
            return {"success": self.keyboard_action(kwargs.get("action_type", ""), **kwargs)}
        elif action == "mouse":
            return {"success": self.mouse_action(kwargs.get("action_type", ""), **kwargs)}
        elif action == "file_op":
            return self.file_operation(kwargs.get("operation", ""), **kwargs)
        return {"success": False, "message": "Unknown action"}
