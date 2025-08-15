"""
System Controller for Windows automation
Handles opening applications, file operations, and system control
"""

import pyautogui
import pywinauto
from pywinauto import Application
import subprocess
import os
import time
import psutil
import logging
from typing import Dict, List, Optional
from .app_discovery import discover_installed_apps, resolve_app

class SystemController:
    def __init__(self):
        # Configure PyAutoGUI for safety
        pyautogui.PAUSE = 0.5
        pyautogui.FAILSAFE = True
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self._app_registry: List[Dict] = discover_installed_apps(rescan=False)
        
        # Common application paths
        self.app_paths = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "file manager": "explorer.exe",
            "explorer": "explorer.exe",
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
            "vs code": r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe".format(os.getenv('USERNAME')),
            "cmd": "cmd.exe",
            "powershell": "powershell.exe"
        }
    
    def open_application(self, app_name: str) -> bool:
        """Open an application by name"""
        try:
            # First try discovered apps
            if self.open_discovered_app(app_name):
                return True
                
            app_name_lower = app_name.lower()
            
            # Check if it's a known application
            if app_name_lower in self.app_paths:
                app_path = self.app_paths[app_name_lower]
                
                # Handle special cases
                if app_name_lower == "file manager" or app_name_lower == "explorer":
                    subprocess.Popen(["explorer.exe"])
                elif app_path.endswith(".exe") and not os.path.exists(app_path):
                    # Try to run as system command
                    subprocess.Popen([app_path])
                else:
                    subprocess.Popen([app_path])
                
                self.logger.info(f"Opened application: {app_name}")
                print(f"✅ Opened {app_name}")
                return True
            
            else:
                # Try to open using Windows Run dialog
                return self._open_via_run_dialog(app_name)
                
        except Exception as e:
            self.logger.error(f"Failed to open {app_name}: {e}")
            print(f"❌ Failed to open {app_name}: {e}")
            return False
    
    def _open_via_run_dialog(self, app_name: str) -> bool:
        """Open application via Windows Run dialog"""
        try:
            # Open Run dialog
            pyautogui.hotkey('win', 'r')
            time.sleep(1)
            
            # Type application name
            pyautogui.write(app_name)
            pyautogui.press('enter')
            
            print(f"✅ Attempted to open {app_name} via Run dialog")
            return True
            
        except Exception as e:
            print(f"❌ Failed to open {app_name} via Run dialog: {e}")
            return False
    
    def close_application(self, app_name: str) -> bool:
        """Close an application by name"""
        try:
            # Find running processes
            for process in psutil.process_iter(['pid', 'name']):
                if app_name.lower() in process.info['name'].lower():
                    process.terminate()
                    self.logger.info(f"Closed application: {app_name}")
                    print(f"✅ Closed {app_name}")
                    return True
            
            print(f"⚠️ Application {app_name} not found running")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to close {app_name}: {e}")
            print(f"❌ Failed to close {app_name}: {e}")
            return False
    
    def minimize_application(self, app_name: str) -> bool:
        """Minimize an application window"""
        try:
            # Find and minimize window
            windows = pywinauto.findwindows.find_windows(title_re=f".*{app_name}.*")
            if windows:
                for window_handle in windows:
                    window = pywinauto.application.Application().connect(handle=window_handle).window(handle=window_handle)
                    window.minimize()
                print(f"✅ Minimized {app_name}")
                return True
            else:
                print(f"⚠️ No window found for {app_name}")
                return False
        except Exception as e:
            print(f"❌ Failed to minimize {app_name}: {e}")
            return False

    def maximize_application(self, app_name: str) -> bool:
        """Maximize an application window"""
        try:
            windows = pywinauto.findwindows.find_windows(title_re=f".*{app_name}.*")
            if windows:
                for window_handle in windows:
                    window = pywinauto.application.Application().connect(handle=window_handle).window(handle=window_handle)
                    window.maximize()
                print(f"✅ Maximized {app_name}")
                return True
            else:
                print(f"⚠️ No window found for {app_name}")
                return False
        except Exception as e:
            print(f"❌ Failed to maximize {app_name}: {e}")
            return False
    
    def create_folder(self, folder_path: str) -> bool:
        """Create a new folder"""
        try:
            os.makedirs(folder_path, exist_ok=True)
            print(f"✅ Created folder: {folder_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to create folder {folder_path}: {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file (with confirmation)"""
        try:
            if os.path.exists(file_path):
                try:
                    from send2trash import send2trash
                    send2trash(file_path)
                    print(f"✅ Moved to recycle bin: {file_path}")
                    return True
                except ImportError:
                    # Fallback to os.remove if send2trash not available
                    os.remove(file_path)
                    print(f"✅ Deleted file: {file_path}")
                    return True
            else:
                print(f"⚠️ File not found: {file_path}")
                return False
        except Exception as e:
            print(f"❌ Failed to delete {file_path}: {e}")
            return False
    
    def get_running_applications(self) -> List[str]:
        """Get list of currently running applications"""
        try:
            running_apps = []
            for process in psutil.process_iter(['pid', 'name']):
                app_name = process.info['name']
                if app_name.endswith('.exe'):
                    app_name = app_name[:-4]  # Remove .exe extension
                if app_name not in running_apps and len(app_name) > 2:
                    running_apps.append(app_name)
            
            return sorted(running_apps)
        except Exception as e:
            print(f"❌ Failed to get running applications: {e}")
            return []
    
    def take_screenshot(self, save_path: Optional[str] = None) -> str:
        """Take a screenshot of the screen"""
        try:
            if not save_path:
                save_path = f"screenshot_{int(time.time())}.png"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(save_path)
            
            print(f"✅ Screenshot saved: {save_path}")
            return save_path
        except Exception as e:
            print(f"❌ Failed to take screenshot: {e}")
            return ""
    
    def type_text(self, text: str) -> bool:
        """Type text at current cursor position"""
        try:
            pyautogui.write(text)
            print(f"✅ Typed text: {text[:50]}...")
            return True
        except Exception as e:
            print(f"❌ Failed to type text: {e}")
            return False
    
    def press_key_combination(self, keys: str) -> bool:
        """Press key combination (e.g., 'ctrl+c', 'win+r')"""
        try:
            key_parts = keys.lower().split('+')
            pyautogui.hotkey(*key_parts)
            print(f"✅ Pressed key combination: {keys}")
            return True
        except Exception as e:
            print(f"❌ Failed to press keys {keys}: {e}")
            return False

    def refresh_app_registry(self) -> int:
        """Rescan Program Files and refresh internal app registry."""
        self._app_registry = discover_installed_apps(rescan=True)
        return len(self._app_registry)

    def list_discovered_apps(self, limit: int = 50) -> List[str]:
        names = [a['app_name'] for a in self._app_registry]
        return names[:limit]

    def open_discovered_app(self, name: str) -> bool:
        app = resolve_app(name, self._app_registry)
        if not app:
            print(f"⚠️ Could not resolve application: {name}")
            return False
        try:
            os.startfile(app['main_exe'])
            print(f"✅ Opened {app['app_name']}")
            return True
        except Exception as e:
            print(f"❌ Failed to open {app['app_name']}: {e}")
            return False

# Test function
def test_system_controller():
    """Test the system controller"""
    controller = SystemController()
    
    print("Testing System Controller...")
    
    # Test opening notepad
    if controller.open_application("notepad"):
        time.sleep(2)
        
        # Test typing text
        controller.type_text("Hello from AI Assistant!")
        time.sleep(2)
        
        # Test key combination
        controller.press_key_combination("ctrl+a")
        time.sleep(1)
        
        # Test closing
        controller.close_application("notepad")

if __name__ == "__main__":
    test_system_controller()
