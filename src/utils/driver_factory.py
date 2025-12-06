from pywinauto import Application, Desktop
import time
from typing import Optional

class DriverFactory:
    _app: Optional[Application] = None
    _backend: str = "uia" # Default backend

    @classmethod
    def get_app(cls) -> Application:
        if cls._app is None:
            # If not connected, we might return None or raise. 
            # Ideally we should start or connect. 
            # For simplicity, returning None if not explicitly started.
            raise RuntimeError("Application not started. Call start_app or connect_app first.")
        return cls._app

    @classmethod
    def start_app(cls, path: str, backend: str = "uia", timeout: int = 10):
        cls._backend = backend
        cls._app = Application(backend=backend).start(path, timeout=timeout)
        time.sleep(1) # Wait for stability
        return cls._app

    @classmethod
    def connect_app(cls, **kwargs):
        """
        Connect to an existing application. 
        kwargs can be path, title, handle, etc.
        Example: connect_app(path=r"C:\Windows\System32\notepad.exe")
        """
        backend = kwargs.pop('backend', 'uia')
        cls._backend = backend
        cls._app = Application(backend=backend).connect(**kwargs)
        return cls._app

    @classmethod
    def close_app(cls):
        if cls._app:
            try:
                cls._app.kill()
            except Exception:
                pass
            cls._app = None
