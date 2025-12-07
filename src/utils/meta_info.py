
import os
import sys
import platform
import subprocess
import json
import socket
import getpass
import logging
from datetime import datetime, timezone

def run_powershell(command):
    try:
        result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        logging.warning(f"Failed to run PowerShell command '{command}': {e}")
        return "Unknown"

def get_git_info():
    try:
        branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
        return {"git_branch": branch, "git_commit": commit}
    except Exception:
        return {"git_branch": "unknown", "git_commit": "unknown"}

def get_env_info():
    # OS Info via PowerShell as requested or fallback
    try:
        # Get-CimInstance -ClassName Win32_OperatingSystem | Select-Object -Property Caption, Version
        # We can format it as JSON for easier parsing or just get specific fields
        os_name = run_powershell("(Get-CimInstance -ClassName Win32_OperatingSystem).Caption")
        os_version = run_powershell("(Get-CimInstance -ClassName Win32_OperatingSystem).Version")
        
        # DPI
        dpi = run_powershell("Get-CimInstance Win32_DesktopMonitor | Select-Object -ExpandProperty PixelsPerXLogicalInch")
        if not dpi or dpi == "Unknown":
            # Fallback for DPI if Win32_DesktopMonitor fails (common on some modern Windows)
             dpi = run_powershell("Get-GraphicsCache | Select-Object -First 1 -ExpandProperty VerticalResolution") # This is not DPI.
             # Better DPI approach commonly used in PS scripts
             dpi = run_powershell("[System.Drawing.Graphics]::FromHwnd([IntPtr]::Zero).DpiX")

        # Resolution
        # Get-CimInstance Win32_VideoController
        res_h = run_powershell("(Get-CimInstance Win32_VideoController).CurrentHorizontalResolution")
        res_v = run_powershell("(Get-CimInstance Win32_VideoController).CurrentVerticalResolution")
        resolution = f"{res_h}x{res_v}" if res_h != "Unknown" and res_v != "Unknown" else "Unknown"
        
        # Python
        python_ver = platform.python_version()
        
        # Pywinauto version if installed
        try:
            import pywinauto
            pywinauto_ver = pywinauto.__version__
        except ImportError:
            pywinauto_ver = "Not Installed"

        return {
            "os_name": os_name,
            "os_version": os_version,
            "locale": run_powershell("Get-Culture | Select-Object -ExpandProperty Name"),
            "dpi": dpi,
            "resolution": resolution,
            "python": python_ver,
            "pywinauto": pywinauto_ver
        }
    except Exception as e:
        logging.error(f"Error gathering env info: {e}")
        return {}

def collect_meta_info(run_id, cases_stats, artifacts_paths):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    executor = {
        "user": getpass.getuser(),
        "trigger": "manual", # Default as per request
        "host": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname())
    }
    
    env = get_env_info()
    source = get_git_info()
    
    meta_data = {
        "run_id": run_id,
        "timestamp": timestamp,
        "executor": executor,
        "env": env,
        "source": source,
        "cases": cases_stats,
        "artifacts": artifacts_paths
    }
    
    return meta_data
