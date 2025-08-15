import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.controllers.app_discovery import discover_installed_apps, resolve_app

def main():
    print("Testing App Discovery...")
    
    # Test discovery
    print("\n1. Discovering installed apps...")
    apps = discover_installed_apps(rescan=True)
    print(f"Discovered {len(apps)} apps")
    
    # Show first 20 apps
    print("\n2. First 20 discovered apps:")
    for i, app in enumerate(apps[:20], 1):
        print(f"{i:2d}. {app['app_name']} | {app['vendor']} | {os.path.basename(app['main_exe'])}")
    
    # Test resolution
    print("\n3. Testing app resolution:")
    test_queries = ["chrome", "google chrome", "firefox", "visual studio code", "word", "excel", "notepad++"]
    
    for query in test_queries:
        app = resolve_app(query, apps)
        if app:
            print(f"✅ Resolved '{query}' -> {app['app_name']} ({app['main_exe']})")
        else:
            print(f"❌ Could not resolve '{query}'")
    
    # Test cache functionality
    print("\n4. Testing cache (should be faster):")
    cached_apps = discover_installed_apps(rescan=False)
    print(f"Cached discovery found {len(cached_apps)} apps")
    
    print("\n✅ App discovery test completed!")

if __name__ == "__main__":
    main() 