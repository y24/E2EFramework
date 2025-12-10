#!/usr/bin/env python3
"""
Pywinauto demo: drive Windows Calculator by auto_id with rich diagnostics.
Logs top-level window info (title/class/control_type/auto_id/PID) to help locate
modern Windows 10/11 calculator windows, then clicks buttons via auto_id.
"""
import sys
import time
from pywinauto import Desktop
from pywinauto.application import Application


def click_button(window, auto_id, label, timeout=10):
    """Click a Calculator button using its auto_id."""
    ctrl = window.child_window(auto_id=auto_id, control_type="Button")
    ctrl.wait("enabled", timeout=timeout)
    print(f"Clicking {label} (auto_id='{auto_id}') ...")
    ctrl.click_input()


def find_calculator_window(app):
    """Locate the Calculator window with detailed enumeration output."""
    target_pid = app.process
    desktop = Desktop(backend="uia")

    print(f"calc.exe PID: {target_pid}")
    print("Enumerating top-level UIA windows (title / class / control_type / pid / auto_id):")
    windows = desktop.windows()
    candidates = []
    for w in windows:
        try:
            title = w.window_text()
            cls = w.class_name()
            ctrl_type = w.element_info.control_type
            pid = w.process_id()
            auto_id = w.element_info.automation_id
            print(f"  - '{title}' / {cls} / {ctrl_type} / pid={pid} / auto_id={auto_id}")
            if pid == target_pid:
                candidates.append(w)
            elif title and ("電卓" in title or "Calculator" in title):
                candidates.append(w)
        except Exception:
            continue

    if candidates:
        # Prefer same PID, else first title match.
        for w in candidates:
            try:
                if w.process_id() == target_pid:
                    w.wait("visible", timeout=10)
                    return w
            except Exception:
                continue
        # fallback: first candidate that becomes visible
        for w in candidates:
            try:
                w.wait("visible", timeout=10)
                return w
            except Exception:
                continue

    # Last-resort: regex search over all top-level windows
    print("Falling back to regex search over all windows ...")
    win = desktop.window(title_re=r".*電卓.*|.*Calculator.*")
    win.wait("visible", timeout=10)
    return win


def main():
    print("Starting Calculator via UI Automation backend ...")
    app = Application(backend="uia").start("calc.exe")
    time.sleep(1)  # give the UWP shell a moment to create the top window

    print('Searching for the Calculator window ("電卓" / "Calculator") ...')
    win = find_calculator_window(app)
    print(f'Attached to window: "{win.window_text()}" (class={win.class_name()}, control_type={win.element_info.control_type}).\n')

    # 7 + 3 = 10
    click_button(win, "num7Button", "7")
    click_button(win, "plusButton", "+")
    click_button(win, "num3Button", "3")
    click_button(win, "equalButton", "=")

    # Read the result text announced by the calculator.
    result = win.child_window(auto_id="CalculatorResults", control_type="Text")
    result.wait("visible", timeout=5)
    result_text = result.window_text().strip()
    print(f"Result text from CalculatorResults: '{result_text}'\n")

    print("Sleeping 2 seconds before closing Calculator ...")
    time.sleep(2)
    win.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
