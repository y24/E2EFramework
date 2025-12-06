from typing import Dict, Any, Type
from src.core.context import Context
from src.core.execution.actions.base_action import BaseAction

# We will register actions here dynamically or statically
# For now, let's keep it simple with a registry
class ActionDispatcher:
    _registry: Dict[str, Type[BaseAction]] = {}

    @classmethod
    def register(cls, action_type: str, action_class: Type[BaseAction]):
        cls._registry[action_type] = action_class

    def __init__(self, context: Context):
        self.context = context

    def get_action(self, action_type: str) -> BaseAction:
        action_class = self._registry.get(action_type)
        if not action_class:
            raise ValueError(f"Unknown action type: {action_type}")
        
        return action_class(self.context)
