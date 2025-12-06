from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAction(ABC):
    def __init__(self, context):
        self.context = context

    @abstractmethod
    def execute(self, params: Dict[str, Any]):
        """Executes the action with the given parameters."""
        pass
