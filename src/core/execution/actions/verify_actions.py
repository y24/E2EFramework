import os
from typing import Dict, Any
from src.core.execution.actions.base_action import BaseAction
from src.core.execution.actions.action_dispatcher import ActionDispatcher

class VerifyAction(BaseAction):
    def execute(self, params: Dict[str, Any]):
        check_type = params.get('type')
        
        if check_type == 'equals':
            actual = params.get('actual')
            expected = params.get('expected')
            assert actual == expected, f"Verification failed: expected '{expected}', but got '{actual}'"
            
        elif check_type == 'file_exists':
            path = params.get('path')
            assert os.path.exists(path), f"File does not exist: {path}"
            
        elif check_type == 'contains':
            haystack = params.get('text')
            needle = params.get('contains')
            assert needle in haystack, f"Text '{needle}' not found in '{haystack}'"

        else:
            raise ValueError(f"Unknown verify type: {check_type}")

# Registration
ActionDispatcher.register('verify', VerifyAction)
