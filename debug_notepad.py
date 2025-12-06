from pywinauto import Desktop, Application
import time

try:
    print("Starting Notepad...")
    # Just start it, don't rely on the object if it's a wrapper
    Application(backend="uia").start("notepad.exe")
    time.sleep(3)
    
    print("Scanning Desktop windows...")
    desktop = Desktop(backend="uia")
    
    # List all top-level windows
    wins = desktop.windows()
    for w in wins:
        print(f"Window: '{w.window_text()}' Class: '{w.class_name()}'")
        if "pad" in w.window_text() or "メモ帳" in w.window_text():
            print(">>> Found potential Notepad window!")
            w.print_control_identifiers(depth=2)
            
except Exception as e:
    print(f"Error: {e}")
