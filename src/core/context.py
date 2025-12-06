import os
import re
import configparser
from typing import Any, Dict, Optional

class Context:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Context, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.variables: Dict[str, Any] = {}
        self.config = configparser.ConfigParser()
        self._initialized = True

    def load_config(self, config_path: str, env: str = 'DEFAULT'):
        """Loads configuration from an INI file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        self.config.read(config_path)
        
        # Load DEFAULT section first
        if 'DEFAULT' in self.config:
            for key, value in self.config['DEFAULT'].items():
                self.variables[key.upper()] = value

        # Overwrite with environment specific settings
        if env in self.config:
            for key, value in self.config[env].items():
                self.variables[key.upper()] = value

    def set_variable(self, key: str, value: Any):
        """Sets a runtime variable."""
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Gets a variable value."""
        return self.variables.get(key, default)

    def resolve(self, text: str) -> str:
        """Resolves variables in the format ${VAR_NAME} within a string."""
        if not isinstance(text, str):
            return text
        
        def replace(match):
            key = match.group(1)
            return str(self.variables.get(key, match.group(0)))
        
        return re.sub(r'\$\{([a-zA-Z0-9_]+)\}', replace, text)

    def clear(self):
        """Clears all variables (mostly for testing)."""
        self.variables = {}
        self.config = configparser.ConfigParser()
