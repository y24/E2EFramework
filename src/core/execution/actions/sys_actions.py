import time
import subprocess
from typing import Dict, Any
from src.core.execution.actions.base_action import BaseAction
from src.core.execution.actions.action_dispatcher import ActionDispatcher
from src.utils.driver_factory import DriverFactory

class SystemAction(BaseAction):
    def execute(self, params: Dict[str, Any]):
        action = params.get('action')
        
        if action == 'sleep':
            duration = float(params.get('duration', 1.0))
            time.sleep(duration)
        
        elif action == 'command':
            cmd = params.get('command')
            if cmd:
                subprocess.run(cmd, shell=True, check=True)
                
        elif action == 'print':
            message = params.get('message')
            print(f"[SCENARIO OUTPUT] {message}")

        elif action == 'start_app':
            path = params.get('path')
            backend = params.get('backend', 'uia')
            DriverFactory.start_app(path, backend=backend)
            
        else:
            raise ValueError(f"Unknown system action: {action}")

# Registration
ActionDispatcher.register('system', SystemAction)
