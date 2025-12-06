from pywinauto.application import Application
import time

app_path = r"D:\Program Files\Flexible Renamer\Flexible Renamer.exe"
print(f"Starting {app_path}...")
try:
    app = Application(backend="win32").start(app_path)
    time.sleep(3)
    win = app.window(title_re=".*Flexible Renamer.*")
    win.wait('visible', timeout=10)
    
    print("Listing all descendants with class_name='Button':")
    try:
        # descendants() returns a list of wrappers
        buttons = win.descendants(class_name="Button")
        for btn in buttons:
            print(f" - Title: '{btn.window_text()}'")
    except Exception as e2:
        print(f"Error listing descendants: {e2}")

except Exception as e:
    print(f"Error: {e}")
finally:
    try: app.kill()
    except: pass
