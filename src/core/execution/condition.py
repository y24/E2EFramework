from typing import Dict, Any
import re
import importlib
import logging
from src.core.context import Context

class ConditionEvaluator:
    def __init__(self, context: Context):
        self.context = context
        self.logger = logging.getLogger(__name__)

    def evaluate(self, condition: Dict[str, Any]) -> bool:
        """
        Evaluates a condition block.
        Example conditions:
        {
            "type": "variable",
            "key": "IS_LOGGED_IN",
            "operator": "equals",
            "value": "true"
        }
        {
            "type": "element_exists",
            "target": "notepad_page.NotepadPage.save_dialog",
            "expected": true,
            "timeout": 2
        }
        """
        if not condition:
            return True

        cond_type = condition.get('type')

        if cond_type == 'variable':
            return self._evaluate_variable(condition)
        elif cond_type == 'element_exists':
            return self._evaluate_element_exists(condition)
        
        # Unknown condition type - log warning and return True (don't skip step)
        self.logger.warning(f"Unknown condition type: {cond_type}. Condition will be ignored.")
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

    def _evaluate_element_exists(self, condition: Dict[str, Any]) -> bool:
        """
        Evaluates whether a UI element exists.
        
        Args:
            condition: Dictionary containing:
                - target: UI element path (e.g., "notepad_page.NotepadPage.save_dialog")
                - expected: Expected existence state (true/false, default: true)
                - timeout: Time to wait for element (seconds, default: 0)
        
        Returns:
            bool: True if condition is met, False otherwise
        """
        target = condition.get('target')
        expected = condition.get('expected', True)
        timeout = condition.get('timeout', 0)
        
        if not target:
            self.logger.error("element_exists condition requires 'target' parameter")
            return False
        
        # Normalize expected value
        if isinstance(expected, str):
            expected = expected.lower() == 'true'
        
        try:
            # Parse target (format: "module.Class.element")
            parts = target.split('.')
            if len(parts) < 3:
                self.logger.error(f"Invalid target format '{target}'. Expected 'module.Class.element'")
                return False
            
            module_name = parts[0]
            class_name = parts[1]
            element_name = parts[2]
            
            # Dynamic import
            module = importlib.import_module(f"src.pages.{module_name}")
            page_class = getattr(module, class_name)
            page_instance = page_class()
            
            # Get the element
            if not hasattr(page_instance, element_name):
                self.logger.error(f"Page '{class_name}' has no element '{element_name}'")
                return False
            
            element = getattr(page_instance, element_name)
            
            # Check existence with timeout
            exists = False
            if timeout > 0:
                try:
                    element.wait('exists', timeout=timeout)
                    exists = True
                except Exception:
                    exists = False
            else:
                exists = element.exists()
            
            # Compare with expected value
            result = (exists == expected)
            
            self.logger.info(
                f"element_exists condition: target='{target}', "
                f"exists={exists}, expected={expected}, result={result}"
            )
            
            return result
            
        except ImportError as e:
            self.logger.error(f"Could not import page module 'src.pages.{module_name}': {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error evaluating element_exists condition for '{target}': {e}")
            return False
