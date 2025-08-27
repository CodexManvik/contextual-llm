import os
import logging
import subprocess
import psutil
import time
import webbrowser
from typing import Dict, List, Optional, Any
from difflib import get_close_matches

# Windows-specific imports with proper error handling
try:
    import win32gui
    import win32process
    import win32con
    import pyautogui
    import pywinauto
    WINDOWS_AVAILABLE = True
except ImportError:
    win32gui = None
    win32process = None
    win32con = None
    pyautogui = None
    pywinauto = None
    WINDOWS_AVAILABLE = False

# Import our app discovery module
from .app_discovery import DynamicAppDiscovery

class SystemController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app_discovery = DynamicAppDiscovery()
        self.launched_processes: Dict[str, Dict] = {}
        self.app_states: Dict[str, str] = {}
        
        # Launch timeout settings
        self.launch_timeout = 30  # seconds
        self.window_wait_timeout = 10  # seconds
        
        # Setup pyautogui if available
        if WINDOWS_AVAILABLE and pyautogui:
            pyautogui.PAUSE = 0.3
            pyautogui.FAILSAFE = True
    
    def refresh_app_registry(self) -> int:
        """Refresh the dynamic app registry"""
        self.app_discovery.discover_all_applications()
        stats = self.app_discovery.get_app_stats()
        return stats.get("total_apps", 0)
    
    def get_all_available_apps(self) -> List[str]:
        """Get list of all discoverable applications"""
        return [info["name"] for info in self.app_discovery.discovered_apps.values()]
    
    def open_any_application(self, app_name: str) -> Dict[str, Any]:
        """Open any application with robust discovery and launching"""
        if not app_name:
            self.logger.warning("No application name provided.")
            return {
                "success": False,
                "message": "No application name provided.",
                "suggestions": []
            }
            
        self.logger.info(f"Attempting to open application: {app_name}")
        
        # Step 1: Find the application
        app_info = self.app_discovery.find_application(app_name)
        if not app_info or not app_info.get("path"):
            return {
                "success": False,
                "message": f"Could not find application '{app_name}'. Try being more specific.",
                "suggestions": self.get_app_suggestions(app_name)
            }
        
        app_path = app_info["path"]
        app_display_name = app_info["name"]
        
        if not app_path:
            self.logger.warning(f"Application '{app_display_name}' does not have a valid path.")
            return {
                "success": False,
                "message": f"Application '{app_display_name}' does not have a valid executable path.",
                "app_info": app_info
            }
            
        self.logger.info(f"Found application '{app_display_name}' at {app_path}")
        
        # Step 2: Check if already running
        if self.is_app_running(app_display_name):
            # Try to bring existing window to front
            if self.focus_existing_app(app_display_name):
                return {
                    "success": True,
                    "message": f"{app_display_name} was already running. Brought to front.",
                    "app_info": app_info,
                    "action": "focused_existing"
                }
        
        # Step 3: Launch the application
        return self.launch_application(app_path, app_display_name, app_info)
    
    def launch_application(self, app_path: str, app_name: str, app_info: Dict) -> Dict[str, Any]:
        """Launch application with robust error handling"""
        try:
            # Determine launch method based on file type
            if app_info.get("type") == "shortcut":
                return self.launch_via_shortcut(app_info.get("shortcut_path", ""), app_name, app_info)
            else:
                return self.launch_via_executable(app_path, app_name, app_info)
        except PermissionError:
            return {
                "success": False,
                "message": f"Permission denied when trying to launch {app_name}. Try running as administrator.",
                "error_type": "permission_denied"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "message": f"Application executable not found: {app_path}",
                "error_type": "file_not_found"
            }
        except Exception as e:
            error_msg = f"Failed to launch {app_name}: {str(e)}" if app_name else "Failed to launch application"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error_type": "launch_failed"
            }
    
    def launch_via_executable(self, app_path: str, app_name: str, app_info: Dict) -> Dict[str, Any]:
        """Launch application via direct executable"""
        try:
            # Set working directory to app directory
            working_dir = os.path.dirname(app_path)
            
            # Launch with proper working directory
            process = subprocess.Popen(
                [app_path],
                cwd=working_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Track the launched process
            self.launched_processes[app_name] = {
                "process": process,
                "pid": process.pid,
                "launch_time": time.time(),
                "app_info": app_info
            }
            
            # Wait for application window to appear
            if self.wait_for_app_window(app_name):
                return {
                    "success": True,
                    "message": f"Successfully launched {app_name}",
                    "app_info": app_info,
                    "pid": process.pid,
                    "action": "launched_new"
                }
            else:
                return {
                    "success": True,
                    "message": f"Launched {app_name} (window detection timed out)",
                    "app_info": app_info,
                    "pid": process.pid,
                    "action": "launched_new",
                    "warning": "Could not detect application window"
                }
        except Exception as e:
            raise e
    
    def launch_via_shortcut(self, shortcut_path: str, app_name: str, app_info: Dict) -> Dict[str, Any]:
        """Launch application via shortcut"""
        try:
            # Use Windows shell to execute shortcut
            os.startfile(shortcut_path)
            
            # Wait for application to appear
            if self.wait_for_app_window(app_name):
                return {
                    "success": True,
                    "message": f"Successfully launched {app_name} via shortcut",
                    "app_info": app_info,
                    "action": "launched_via_shortcut"
                }
            else:
                return {
                    "success": True,
                    "message": f"Launched {app_name} via shortcut (window detection timed out)",
                    "app_info": app_info,
                    "action": "launched_via_shortcut",
                    "warning": "Could not detect application window"
                }
        except Exception as e:
            raise e
    
    def is_app_running(self, app_name: str) -> bool:
        """Check if application is currently running"""
        if not app_name:
            return False
            
        app_name_lower = app_name.lower()
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_info = proc.info
                    if proc_info['name']:
                        proc_name = os.path.splitext(proc_info['name'])[0].lower()
                        if app_name_lower in proc_name or proc_name in app_name_lower:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            error_msg = f"Error checking if {app_name} is running: {e}" if app_name else "Error checking if application is running"
            self.logger.debug(error_msg)
        return False
    
    def focus_existing_app(self, app_name: str) -> bool:
        """Focus existing application window"""
        if not app_name:
            return False
            
        if not WINDOWS_AVAILABLE or not win32gui or not win32con:
            return False
        
        try:
            def enum_windows_callback(hwnd, app_name):
                if win32gui and win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if app_name.lower() in window_title.lower():
                        # Bring window to front
                        if win32con is not None:
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                        return False  # Stop enumeration
                return True
            
            if win32gui:
                win32gui.EnumWindows(enum_windows_callback, app_name)
                return True
            return False
        except Exception as e:
            error_msg = f"Failed to focus existing {app_name}: {e}" if app_name else "Failed to focus existing application"
            self.logger.debug(error_msg)
            return False
    
    def wait_for_app_window(self, app_name: str, timeout: Optional[int] = None) -> bool:
        """Wait for application window to appear"""
        if not app_name:
            return False
            
        if not WINDOWS_AVAILABLE or not win32gui:
            return False
        
        if timeout is None:
            timeout = self.window_wait_timeout
        
        start_time = time.time()
        app_name_lower = app_name.lower()
        
        while time.time() - start_time < timeout:
            try:
                def enum_windows_callback(hwnd, found):
                    if win32gui and win32gui.IsWindowVisible(hwnd):
                        window_title = win32gui.GetWindowText(hwnd)
                        if window_title and app_name_lower in window_title.lower():
                            found[0] = True
                            return False  # Stop enumeration
                    return True
                
                found = [False]
                if win32gui:
                    win32gui.EnumWindows(enum_windows_callback, found)
                if found[0]:
                    return True
                
                time.sleep(0.5)  # Check every 500ms
            except Exception as e:
                error_msg = f"Error waiting for {app_name} window: {e}" if app_name else "Error waiting for application window"
                self.logger.debug(error_msg)
                break
        
        return False
    
    def get_app_suggestions(self, query: str) -> List[str]:
        """Get suggestions for similar app names"""
        all_app_names = [info["name"] for info in self.app_discovery.discovered_apps.values()]
        suggestions = get_close_matches(query, all_app_names, n=5, cutoff=0.4)
        return suggestions
    
    def close_application(self, app_name: str) -> Dict[str, Any]:
        """Close a running application"""
        if not app_name:
            return {
                "success": False,
                "message": "No application name provided"
            }
            
        app_name_lower = app_name.lower()
        closed_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_info = proc.info
                    if proc_info['name']:
                        proc_name = os.path.splitext(proc_info['name'])[0].lower()
                        if app_name_lower in proc_name or proc_name in app_name_lower:
                            proc.terminate()
                            closed_processes.append(proc_info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if closed_processes:
                return {
                    "success": True,
                    "message": f"Closed {len(closed_processes)} processes for {app_name}",
                    "closed_processes": closed_processes
                }
            else:
                return {
                    "success": False,
                    "message": f"No running processes found for {app_name}"
                }
        except Exception as e:
            error_msg = f"Failed to close {app_name}: {str(e)}" if app_name else "Failed to close application"
            return {
                "success": False,
                "message": error_msg
            }
    
    def web_search(self, query: str) -> Dict[str, Any]:
        """Perform web search"""
        if not query:
            self.logger.error("Web search failed: No query provided.")
            return {
                "success": False,
                "message": "No search query provided"
            }
            
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return {
                "success": True,
                "message": f"Opened web search for: {query}",
                "url": search_url
            }
        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return {
                "success": False,
                "message": f"Web search failed: {str(e)}"
            }
    
    def keyboard_action(self, action_type: str, **kwargs) -> Dict[str, Any]:
        """Perform keyboard actions"""
        if not WINDOWS_AVAILABLE or not pyautogui:
            return {
                "success": False,
                "message": "Keyboard actions not available (Windows-specific modules not loaded)"
            }
        
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
            else:
                return {
                    "success": False,
                    "message": f"Unknown keyboard action: {action_type}"
                }
            
            return {
                "success": True,
                "message": f"Keyboard action '{action_type}' executed"
            }
        except Exception as e:
            self.logger.error(f"Keyboard action failed: {e}")
            return {
                "success": False,
                "message": f"Keyboard action failed: {str(e)}"
            }
    
    def mouse_action(self, action_type: str, **kwargs) -> Dict[str, Any]:
        """Perform mouse actions"""
        if not WINDOWS_AVAILABLE or not pyautogui:
            return {
                "success": False,
                "message": "Mouse actions not available (Windows-specific modules not loaded)"
            }
        
        try:
            if action_type == "click":
                x = kwargs.get("x")
                y = kwargs.get("y")
                if x is not None and y is not None:
                    pyautogui.click(x, y)
                else:
                    pyautogui.click()
            elif action_type == "scroll":
                scrolls = kwargs.get("scrolls", 3)
                pyautogui.scroll(scrolls)
            else:
                return {
                    "success": False,
                    "message": f"Unknown mouse action: {action_type}"
                }
            
            return {
                "success": True,
                "message": f"Mouse action '{action_type}' executed"
            }
        except Exception as e:
            self.logger.error(f"Mouse action failed: {e}")
            return {
                "success": False,
                "message": f"Mouse action failed: {str(e)}"
            }
    
    def file_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Perform file operations"""
        try:
            if operation == "create_folder":
                path = kwargs.get("path", "")
                if not path:
                    return {"success": False, "message": "Path is required for create_folder operation"}
                os.makedirs(path, exist_ok=True)
                return {"success": True, "message": f"Created folder: {path}"}
            
            elif operation == "open_file":
                path = kwargs.get("path", "")
                if not path:
                    return {"success": False, "message": "Path is required for open_file operation"}
                if not os.path.exists(path):
                    return {"success": False, "message": f"File/folder not found: {path}"}
                
                if os.name == 'nt':
                    os.startfile(path)
                else:
                    subprocess.run(['xdg-open', path])
                
                return {"success": True, "message": f"Opened: {path}"}
            
            elif operation == "delete_file":
                path = kwargs.get("path", "")
                if not path:
                    return {"success": False, "message": "Path is required for delete_file operation"}
                if not os.path.exists(path):
                    return {"success": False, "message": f"File/folder not found: {path}"}
                
                if os.path.isfile(path):
                    os.remove(path)
                    return {"success": True, "message": f"Deleted file: {path}"}
                else:
                    return {"success": False, "message": f"Path is not a file: {path}"}
            
            else:
                return {"success": False, "message": f"Unknown file operation: {operation}"}
            
        except Exception as e:
            return {"success": False, "message": f"File operation failed: {str(e)}"}
    
    def execute_with_confirmation(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute actions with confirmation for safety"""
        # Show preview
        preview = self.dry_run_action(action, **kwargs)
        
        # For now, auto-confirm (you can add real confirmation logic here)
        confirmed = True
        
        if confirmed:
            result = self.execute_action(action, **kwargs)
            self.logger.info(f"Action executed: {action}")
            return result
        else:
            return {"success": False, "message": "Action cancelled by user"}
    
    def dry_run_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """Simulate action without executing"""
        return {"preview": f"Would perform {action} with params {kwargs}"}
    
    def execute_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """Core action executor"""
        if action == "open_app":
            return self.open_any_application(kwargs.get("app_name", ""))
        elif action == "web_search":
            return self.web_search(kwargs.get("query", ""))
        elif action == "keyboard":
            return self.keyboard_action(kwargs.get("action_type", ""), **kwargs)
        elif action == "mouse":
            return self.mouse_action(kwargs.get("action_type", ""), **kwargs)
        elif action == "file_op":
            return self.file_operation(kwargs.get("operation", ""), **kwargs)
        else:
            return {"success": False, "message": f"Unknown action: {action}"}
    
    def get_running_apps(self) -> List[Dict]:
        """Get detailed list of running applications"""
        running_apps = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'memory_info', 'create_time']):
                try:
                    proc_info = proc.info
                    if proc_info['exe'] and proc_info['name']:
                        # Filter out system processes
                        if not self.is_system_process(proc_info['name']):
                            app_info = {
                                "name": os.path.splitext(proc_info['name'])[0],
                                "pid": proc_info['pid'],
                                "exe_path": proc_info['exe'],
                                "memory_mb": round(proc_info['memory_info'].rss / 1024 / 1024, 1),
                                "start_time": proc_info['create_time']
                            }
                            running_apps.append(app_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Failed to get running apps: {e}")
        
        return running_apps
    
    def is_system_process(self, process_name: str) -> bool:
        """Check if process is a system process to filter out"""
        system_processes = [
            'explorer.exe', 'dwm.exe', 'winlogon.exe', 'csrss.exe', 'smss.exe',
            'wininit.exe', 'services.exe', 'lsass.exe', 'svchost.exe', 'audiodg.exe',
            'conhost.exe'
        ]
        return process_name.lower() in system_processes
    
    def get_focused_window(self) -> Optional[Dict]:
        """Get information about currently focused window"""
        if not WINDOWS_AVAILABLE or not win32gui or not win32process:
            return None
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                window_title = win32gui.GetWindowText(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    return {
                        "window_title": window_title,
                        "process_name": process.name(),
                        "pid": pid,
                        "exe_path": process.exe()
                    }
                except psutil.NoSuchProcess:
                    return None
        except Exception as e:
            self.logger.debug(f"Failed to get focused window: {e}")
        
        return None
    
    def refresh_app_discovery(self) -> Dict[str, Any]:
        """Force refresh of application discovery"""
        try:
            self.app_discovery.discover_all_applications()
            stats = self.app_discovery.get_app_stats()
            return {
                "success": True,
                "message": f"Refreshed application discovery. Found {stats['total_apps']} applications.",
                "stats": stats
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to refresh app discovery: {str(e)}"
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information and statistics"""
        return {
            "discovered_apps": self.app_discovery.get_app_stats(),
            "running_apps": len(self.get_running_apps()),
            "launched_processes": len(self.launched_processes),
            "focused_window": self.get_focused_window(),
        }

    def set_intelligent_controller(self, intelligent_controller):
        """Set the intelligent app controller for advanced task execution"""
        self.intelligent_controller = intelligent_controller
        self.logger.info("Intelligent app controller set successfully")

    def execute_intelligent_task(self, app_name: str, user_intent: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute intelligent task using AI-powered controller"""
        if not hasattr(self, 'intelligent_controller') or not self.intelligent_controller:
            return {
                "success": False,
                "message": "Intelligent controller not available",
                "fallback_available": True
            }

        try:
            # First, ensure the application is open
            app_info = self.app_discovery.find_application(app_name)
            if not app_info or not app_info.get("path"):
                return {
                    "success": False,
                    "message": f"Could not find application '{app_name}'",
                    "suggestions": self.get_app_suggestions(app_name)
                }

            # Check if app is already running, if not, launch it
            if not self.is_app_running(app_name):
                launch_result = self.open_any_application(app_name)
                if not launch_result.get("success", False):
                    return {
                        "success": False,
                        "message": f"Failed to launch {app_name}: {launch_result.get('message', 'Unknown error')}",
                        "launch_failed": True
                    }

                # Wait a moment for the app to fully launch
                time.sleep(2)

            # Execute the intelligent task
            task_context = context if context is not None else self._build_task_context(app_name)

            result = self.intelligent_controller.execute_intelligent_task(app_name, user_intent, task_context)
            
            # Add app info to result
            result["app_info"] = app_info
            return result

        except Exception as e:
            self.logger.error(f"Intelligent task execution failed: {e}")
            return {
                "success": False,
                "message": f"Intelligent task failed: {str(e)}",
                "error_type": "intelligent_execution_error"
            }

    def _build_task_context(self, app_name: str) -> Dict[str, Any]:
        """Build context for intelligent task execution"""
        return {
            "system_state": {
                "running_apps": [app.name() for app in psutil.process_iter(['name']) if app.info['name']],
                "focused_window": self.get_focused_window(),
                "available_apps": self.get_all_available_apps()
            },
            "app_context": {
                "is_running": self.is_app_running(app_name),
                "window_focused": self._is_app_focused(app_name),
                "recent_interactions": self._get_recent_app_interactions(app_name)
            },
            "user_context": {
                "preferences": {},
                "usage_patterns": self._get_app_usage_patterns(app_name)
            }
        }

    def _is_app_focused(self, app_name: str) -> bool:
        """Check if the application window is currently focused"""
        focused = self.get_focused_window()
        if focused and focused.get("process_name"):
            return app_name.lower() in focused["process_name"].lower()
        return False

    def _get_recent_app_interactions(self, app_name: str) -> List[Dict]:
        """Get recent interactions with the application"""
        # This would be populated by the intelligent controller
        return []

    def _get_app_usage_patterns(self, app_name: str) -> Dict:
        """Get usage patterns for the application"""
        # This would track how the user typically uses this app
        return {}

    def debug_app_discovery(self) -> None:
        """Debug method to check app discovery"""
        try:
            self.logger.info("=== APP DISCOVERY DEBUG ===")
            
            # Force refresh
            self.app_discovery.discover_all_applications()
            
            # List all discovered apps
            all_apps = self.get_all_available_apps()
            self.logger.info(f"Total discovered apps: {len(all_apps)}")
            
            for app in all_apps[:10]:  # Log first 10
                self.logger.info(f"  - {app}")
                
            # Test specific apps
            test_apps = ['notepad', 'firefox', 'chrome', 'calculator', 'word', 'excel']
            for test_app in test_apps:
                app_info = self.app_discovery.find_application(test_app)
                if app_info:
                    self.logger.info(f"✓ Found {test_app}: {app_info.get('path')}")
                else:
                    self.logger.warning(f"✗ Could not find {test_app}")
                    
        except Exception as e:
            self.logger.error(f"App discovery debug failed: {e}")
