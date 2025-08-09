import pyautogui
import pywinauto
import time
import subprocess

# Configure PyAutoGUI safety
pyautogui.PAUSE = 1
pyautogui.FAILSAFE = True

def test_basic_automation():
    print("Testing basic system automation...")
    
    # Test 1: Mouse movement
    print("1. Testing mouse movement...")
    current_pos = pyautogui.position()
    print(f"Current mouse position: {current_pos}")
    
    # Move mouse in a small square
    pyautogui.moveTo(current_pos.x + 100, current_pos.y, duration=1)
    pyautogui.moveTo(current_pos.x + 100, current_pos.y + 100, duration=1)
    pyautogui.moveTo(current_pos.x, current_pos.y + 100, duration=1)
    pyautogui.moveTo(current_pos.x, current_pos.y, duration=1)
    
    # Test 2: Keyboard input
    print("2. Testing keyboard automation...")
    print("Opening Notepad in 3 seconds... (Close it manually after test)")
    time.sleep(3)
    
    # Open notepad
    pyautogui.hotkey('win', 'r')
    time.sleep(1)
    pyautogui.write('notepad')
    pyautogui.press('enter')
    time.sleep(2)
    
    # Type test message
    test_message = "Hello! This is a test from your AI assistant."
    pyautogui.write(test_message)
    
    print("Test completed! Close Notepad manually.")

def test_application_control():
    print("Testing application control with pywinauto...")
    
    try:
        # Connect to an existing notepad or start new one
        app = pywinauto.Application(backend="uia")
        
        # Try to connect to existing notepad
        try:
            app.connect(title_re=".*Notepad")
            print("Connected to existing Notepad")
        except:
            # Start new notepad if none exists
            subprocess.Popen(['notepad.exe'])
            time.sleep(2)
            app.connect(title_re=".*Notepad")
            print("Started new Notepad")
        
        # Get the main window
        notepad = app.top_window()
        notepad.set_focus()
        
        # Type in notepad using pywinauto
        edit_control = notepad.child_window(class_name="Edit")
        edit_control.type_keys("This text was typed using pywinauto!")
        
        print("Application control test completed!")
        
    except Exception as e:
        print(f"Application control test failed: {e}")

if __name__ == "__main__":
    print("Starting system control tests...")
    print("Make sure no important work is open, as this will control your mouse/keyboard!")
    
    user_input = input("Press Enter to continue or Ctrl+C to cancel...")
    
    test_basic_automation()
    time.sleep(2)
    test_application_control()
    
    print("\nAll tests completed!")
