import os
import logging
import subprocess
import psutil
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from difflib import SequenceMatcher
import threading
import time
import re
import webbrowser

# Windows-specific imports with robust handling
try:
    import winreg
    import pythoncom
    from win32com.shell import shell, shellcon
    WINDOWSAVAILABLE = True
except ImportError:
    winreg = None
    pythoncom = None
    shell = None
    shellcon = None
    WINDOWSAVAILABLE = False

class DynamicAppDiscovery:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.discovered_apps: Dict[str, Dict] = {}
        self.app_cache_file = "config/app_cache.json"
        self.last_scan_time = 0
        self.scan_interval = 3600  # Rescan every hour
        # Aliases
        self.app_aliases = {
            "firefox": "firefox", "fierfox": "firefox",
            "chrome": "google chrome", "word": "microsoft word",
            "excel": "microsoft excel", "powerpoint": "microsoft powerpoint",
            "vs code": "visual studio code", "vscode": "visual studio code",
            "notepad++": "notepad plus plus", "discord": "discord",
            "spotify": "spotify", "slack": "slack",
            "teams": "microsoft teams", "outlook": "microsoft outlook",
            "calc": "calculator", "paint": "microsoft paint",
            "cmd": "command prompt", "powershell": "windows powershell",
            "explorer": "windows explorer", "edge": "microsoft edge",
            "photoshop": "adobe photoshop", "illustrator": "adobe illustrator",
            "premiere": "adobe premiere pro", "after effects": "adobe after effects",
            "steam": "steam", "origin": "origin", "epic": "epic games launcher",
            "blender": "blender", "obs": "obs studio", "vlc": "vlc media player",
            "7zip": "7-zip", "winrar": "winrar"
        }
        self.load_app_cache()
        self.scanning_thread = threading.Thread(target=self.background_scanner, daemon=True)
        self.scanning_thread.start()

    def load_app_cache(self):
        try:
            if os.path.exists(self.app_cache_file):
                with open(self.app_cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    self.discovered_apps = cache_data.get("apps", {})
                    self.last_scan_time = cache_data.get("last_scan", 0)
                    self.logger.info(f"Loaded {len(self.discovered_apps)} apps from cache")
        except Exception as e:
            self.logger.error(f"Failed to load app cache: {e}")

    def save_app_cache(self):
        try:
            os.makedirs(os.path.dirname(self.app_cache_file), exist_ok=True)
            cache_data = {
                "apps": self.discovered_apps,
                "last_scan": time.time(),
                "version": "1.0"
            }
            with open(self.app_cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save app cache: {e}")

    def background_scanner(self):
        while True:
            try:
                current_time = time.time()
                if current_time - self.last_scan_time > self.scan_interval:
                    self.logger.info("Starting background app discovery scan...")
                    self.discover_all_applications()
                    self.last_scan_time = current_time
                    self.save_app_cache()
                time.sleep(300)
            except Exception as e:
                self.logger.error(f"Background scanner error: {e}")
                time.sleep(300)

    def discover_all_applications(self) -> Dict[str, Dict]:
        if not WINDOWSAVAILABLE:
            self.logger.warning("Windows-specific modules not available. Limited functionality.")
            return self.discovered_apps
        self.logger.info("Starting comprehensive app discovery...")
        self.discovered_apps = {}
        self.scan_start_menu()
        self.scan_registry_uninstall()
        self.scan_program_files()
        self.scan_path_executables()
        self.scan_common_locations()
        self.logger.info(f"Discovery complete. Found {len(self.discovered_apps)} applications")
        return self.discovered_apps

    def scan_start_menu(self):
        if not WINDOWSAVAILABLE:
            return
        start_menu_paths = [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu"),
            os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu"),
            os.path.expanduser(r"~\Desktop")
        ]
        for base_path in start_menu_paths:
            if not os.path.exists(base_path):
                continue
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        shortcut_path = os.path.join(root, file)
                        self.process_shortcut(shortcut_path)

    def process_shortcut(self, shortcut_path: str):
        if not WINDOWSAVAILABLE:
            return
        try:
            import win32com.client
            if pythoncom is not None:
                pythoncom.CoInitialize()
            shell_obj = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell_obj.CreateShortcut(shortcut_path)
            target_path = shortcut.TargetPath
            if target_path and os.path.exists(target_path):
                app_name = os.path.splitext(os.path.basename(shortcut_path))[0]
                app_name = self.clean_app_name(app_name)
                if app_name and self.is_valid_executable(target_path):
                    self.discovered_apps[app_name.lower()] = {
                        "name": app_name,
                        "path": target_path,
                        "type": "shortcut",
                        "source": "start_menu",
                        "shortcut_path": shortcut_path
                    }
        except Exception as e:
            self.logger.debug(f"Failed to process shortcut {shortcut_path}: {e}")
        finally:
            try:
                if pythoncom is not None:
                    pythoncom.CoUninitialize()
            except Exception:
                pass
            
    def web_search(self, query: str) -> bool:
        """Perform web search"""
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return True
        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return False
        
    def scan_registry_uninstall(self):
        if not WINDOWSAVAILABLE or winreg is None:
            return
        uninstall_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        for hkey, key_path in uninstall_keys:
            try:
                with winreg.OpenKey(hkey, key_path, 0, winreg.KEY_READ) as reg_key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(reg_key, i)
                            self.process_registry_app(hkey, f"{key_path}\\{subkey_name}")
                            i += 1
                        except OSError:
                            break
            except Exception as e:
                self.logger.debug(f"Failed to scan registry key {key_path}: {e}")

    def process_registry_app(self, hkey, key_path: str):
        if not WINDOWSAVAILABLE or winreg is None:
            return
        try:
            with winreg.OpenKey(hkey, key_path, 0, winreg.KEY_READ) as reg_key:
                try:
                    display_name, _ = winreg.QueryValueEx(reg_key, "DisplayName")
                    display_name = self.clean_app_name(display_name)
                    if self.should_skip_app(display_name):
                        return
                    exe_path = None
                    try:
                        install_location, _ = winreg.QueryValueEx(reg_key, "InstallLocation")
                        if install_location and os.path.exists(install_location):
                            exe_path = self.find_executable_in_directory(install_location, display_name)
                    except FileNotFoundError:
                        pass
                    if not exe_path:
                        try:
                            display_icon, _ = winreg.QueryValueEx(reg_key, "DisplayIcon")
                            if display_icon and display_icon.endswith(".exe") and os.path.exists(display_icon):
                                exe_path = display_icon
                        except FileNotFoundError:
                            pass
                    if not exe_path:
                        try:
                            uninstall_string, _ = winreg.QueryValueEx(reg_key, "UninstallString")
                            if uninstall_string:
                                exe_path = self.extract_exe_from_uninstall(uninstall_string)
                        except FileNotFoundError:
                            pass
                    if exe_path and self.is_valid_executable(exe_path):
                        key = display_name.lower()
                        if key not in self.discovered_apps:
                            self.discovered_apps[key] = {
                                "name": display_name,
                                "path": exe_path,
                                "type": "installed_program",
                                "source": "registry"
                            }
                except FileNotFoundError:
                    pass
        except Exception as e:
            self.logger.debug(f"Failed to process registry app {key_path}: {e}")

    def scan_program_files(self):
        program_dirs = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
        ]
        for program_dir in program_dirs:
            if not program_dir or not os.path.exists(program_dir):
                continue
            try:
                for item in os.listdir(program_dir):
                    item_path = os.path.join(program_dir, item)
                    if os.path.isdir(item_path):
                        exe_path = self.find_executable_in_directory(item_path, item)
                        if exe_path:
                            app_name = self.clean_app_name(item)
                            key = app_name.lower()
                            if key not in self.discovered_apps:
                                self.discovered_apps[key] = {
                                    "name": app_name,
                                    "path": exe_path,
                                    "type": "program_files",
                                    "source": "program_files"
                                }
            except Exception as e:
                self.logger.debug(f"Failed to scan {program_dir}: {e}")

    def scan_path_executables(self):
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        for path_dir in path_dirs:
            if not path_dir or not os.path.exists(path_dir):
                continue
            try:
                for file in os.listdir(path_dir):
                    if file.lower().endswith(".exe"):
                        exe_path = os.path.join(path_dir, file)
                        if self.is_valid_executable(exe_path):
                            app_name = self.clean_app_name(os.path.splitext(file)[0])
                            key = app_name.lower()
                            if key not in self.discovered_apps and not self.should_skip_app(app_name):
                                self.discovered_apps[key] = {
                                    "name": app_name,
                                    "path": exe_path,
                                    "type": "path_executable",
                                    "source": "path"
                                }
            except Exception as e:
                self.logger.debug(f"Failed to scan PATH directory {path_dir}: {e}")

    def scan_common_locations(self):
        common_locations = [
            os.path.expanduser("~/AppData/Local"),
            os.path.expanduser("~/AppData/Roaming"),
            r"C:\Tools", r"C:\Program Files\WindowsApps"
        ]
        for location in common_locations:
            if os.path.exists(location):
                self.scan_directory_for_apps(location, max_depth=3)

    def scan_directory_for_apps(self, directory: str, max_depth: int = 2, current_depth: int = 0):
        if current_depth > max_depth:
            return
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path) and item.lower().endswith(".exe"):
                    if self.is_valid_executable(item_path):
                        app_name = self.clean_app_name(os.path.splitext(item)[0])
                        key = app_name.lower()
                        if key not in self.discovered_apps and not self.should_skip_app(app_name):
                            self.discovered_apps[key] = {
                                "name": app_name,
                                "path": item_path,
                                "type": "common_location",
                                "source": "common_locations"
                            }
                elif os.path.isdir(item_path):
                    self.scan_directory_for_apps(item_path, max_depth, current_depth + 1)
        except Exception as e:
            self.logger.debug(f"Failed to scan directory {directory}: {e}")

    def find_executable_in_directory(self, directory: str, app_name: str) -> Optional[str]:
        if not os.path.exists(directory):
            return None
        possible_names = [
            f"{app_name}.exe",
            f"{app_name.replace(' ', '')}.exe",
            f"{app_name.replace(' ', '_')}.exe",
            f"{app_name.split()[0]}.exe" if ' ' in app_name else f"{app_name}.exe"
        ]
        for root, dirs, files in os.walk(directory):
            if root.count(os.sep) - directory.count(os.sep) > 2:
                dirs[:] = []
                continue
            for file in files:
                if file.lower().endswith(".exe"):
                    file_path = os.path.join(root, file)
                    file_lower = file.lower()
                    for pattern in possible_names:
                        if file_lower == pattern.lower():
                            if self.is_valid_executable(file_path):
                                return file_path
                    similarity = SequenceMatcher(None, app_name.lower(), file_lower).ratio()
                    if similarity > 0.6 and self.is_valid_executable(file_path):
                        return file_path
        return None

    def extract_exe_from_uninstall(self, uninstall_string: str) -> Optional[str]:
        quoted_exe = re.search(r'"([^"]+\.exe)"', uninstall_string)
        if quoted_exe:
            exe_path = quoted_exe.group(1)
            if os.path.exists(exe_path):
                return exe_path
        exe_match = re.search(r'([^\s]+\.exe)', uninstall_string)
        if exe_match:
            exe_path = exe_match.group(1)
            if os.path.exists(exe_path):
                return exe_path
        return None

    def clean_app_name(self, name: str) -> str:
        if not name:
            return ""
        removals = [
            " - Shortcut", ".lnk", ".exe", "™", "®", "©",
            "Microsoft ", "Adobe ", "Google ", "Mozilla ",
            "2024", "2023", "2022", "2021", "2020"
        ]
        cleaned = name
        for removal in removals:
            cleaned = cleaned.replace(removal, "")
        cleaned = re.sub(r' v?\d+(\.\d+)*', '', cleaned)
        cleaned = re.sub(r' \d{4}', '', cleaned)
        return cleaned.strip()

    def should_skip_app(self, app_name: str) -> bool:
        skip_patterns = [
            "microsoft visual c++", "microsoft .net", ".net framework",
            "visual studio", "redistributable", "runtime", "kb", "hotfix",
            "security update", "windows update", "driver", "uninstall",
            "setup", "installer", "maintainance", "repair"
        ]
        app_lower = app_name.lower()
        return any(pattern in app_lower for pattern in skip_patterns)

    def is_valid_executable(self, exe_path: str) -> bool:
        if not exe_path or not os.path.exists(exe_path):
            return False
        try:
            if not exe_path.lower().endswith('.exe'):
                return False
            if os.path.getsize(exe_path) < 10000:
                return False
            with open(exe_path, 'rb') as f:
                header = f.read(2)
                if header != b'MZ':
                    return False
            return True
        except Exception:
            return False

    def find_application(self, query: str) -> Optional[Dict]:
        if not query:
            return None
        query_lower = query.lower().strip()
        if query_lower in self.app_aliases:
            query_lower = self.app_aliases[query_lower]
        if query_lower in self.discovered_apps:
            return self.discovered_apps[query_lower]
        best_match = None
        best_score = 0.0
        for app_key, app_info in self.discovered_apps.items():
            score1 = SequenceMatcher(None, query_lower, app_key).ratio()
            score2 = SequenceMatcher(None, query_lower, app_info["name"].lower()).ratio()
            if query_lower in app_key or query_lower in app_info["name"].lower():
                score3 = 0.8
            else:
                score3 = 0.0
            max_score = max(score1, score2, score3)
            if max_score > best_score and max_score > 0.6:
                best_score = max_score
                best_match = app_info
        return best_match

    def get_running_applications(self) -> List[str]:
        running_apps = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_info = proc.info
                    if proc_info['exe'] and proc_info['name']:
                        app_name = self.clean_app_name(
                            os.path.splitext(proc_info['name'])[0]
                        )
                        if app_name and app_name not in running_apps:
                            running_apps.append(app_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Failed to get running applications: {e}")
        return running_apps

    def get_app_stats(self) -> Dict:
        stats = {
            "total_apps": len(self.discovered_apps),
            "by_source": {},
            "by_type": {},
            "last_scan": self.last_scan_time
        }
        for app_info in self.discovered_apps.values():
            source = app_info.get("source", "unknown")
            app_type = app_info.get("type", "unknown")
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            stats["by_type"][app_type] = stats["by_type"].get(app_type, 0) + 1
        return stats
