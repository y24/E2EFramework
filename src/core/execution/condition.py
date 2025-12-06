from typing import Dict, Any
import re
from src.core.context import Context

class ConditionEvaluator:
    def __init__(self, context: Context):
        self.context = context

    def evaluate(self, condition: Dict[str, Any]) -> bool:
        """
        Evaluates a condition block.
        Example condition:
        {
            "type": "variable",
            "key": "IS_LOGGED_IN",
            "operator": "equals",
            "value": "true"
        }
        """
        if not condition:
            return True

        cond_type = condition.get('type')

        if cond_type == 'variable':
            return self._evaluate_variable(condition)
        
        # Add other condition types as needed (e.g. element_exists)
        
        return True

    def _evaluate_variable(self, condition: Dict[str, Any]) -> bool:
        key = condition.get('key')
        operator = condition.get('operator', 'equals')
        expected_value = condition.get('value')
        
        actual_value = self.context.get_variable(key)  # Value might be string "true" or boolean True
        
        # Normalize for comparison if needed (very basic for now)
        if str(actual_value).lower() == 'true': actual_value = True
        elif str(actual_value).lower() == 'false': actual_value = False
        
        if str(expected_value).lower() == 'true': expected_value = True
        elif str(expected_value).lower() == 'false': expected_value = False

        if operator == 'equals':
            return actual_value == expected_value
        elif operator == 'not_equals':
            return actual_value != expected_value
        elif operator == 'contains':
            return str(expected_value) in str(actual_value)
            
        return False
