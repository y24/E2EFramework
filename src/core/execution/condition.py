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
        elif cond_type == 'element_text_empty':
            return self._evaluate_text_empty(condition)
        elif cond_type == 'checkbox_state':
            return self._evaluate_checkbox_state(condition)
        
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
        element = self._resolve_element(target, required_field="element_exists")
        if not element:
            return False
        
        # Normalize expected value
        if isinstance(expected, str):
            expected = expected.lower() == 'true'
        
        # Check existence with timeout
        exists = False
        if timeout > 0:
            try:
                element.wait('exists', timeout=timeout)
                exists = True
            except Exception:
                exists = False
        else:
            try:
                exists = element.exists()
            except Exception as e:
                self.logger.error(f"Error checking existence for '{target}': {e}")
                return False
        
        # Compare with expected value
        result = (exists == expected)
        
        self.logger.info(
            f"element_exists condition: target='{target}', "
            f"exists={exists}, expected={expected}, result={result}"
        )
        
        return result

    def _evaluate_text_empty(self, condition: Dict[str, Any]) -> bool:
        target = condition.get('target')
        expected = condition.get('expected', True)
        
        if isinstance(expected, str):
            expected = expected.lower() == 'true'
        
        element = self._resolve_element(target, required_field="element_text_empty")
        if not element:
            return False
        
        text_value = None
        try:
            text_value = element.get_value()
        except Exception:
            try:
                text_value = element.window_text()
            except Exception as e:
                self.logger.error(f"Error retrieving text for '{target}': {e}")
                return False
        
        is_empty = (text_value is None) or (str(text_value) == '')
        result = (is_empty == expected)
        
        self.logger.info(
            f"element_text_empty condition: target='{target}', "
            f"is_empty={is_empty}, expected={expected}, result={result}"
        )
        
        return result

    def _evaluate_checkbox_state(self, condition: Dict[str, Any]) -> bool:
        target = condition.get('target')
        expected = condition.get('expected', True)
        
        if isinstance(expected, str):
            expected = expected.lower() == 'true'
        
        element = self._resolve_element(target, required_field="checkbox_state")
        if not element:
            return False
        
        actual_state = None
        
        # Try get_toggle_state first (returns 0/1/2 typically)
        if hasattr(element, 'get_toggle_state'):
            try:
                toggle_state = element.get_toggle_state()
                if toggle_state in [0, 1]:
                    actual_state = (toggle_state == 1)
                elif isinstance(toggle_state, bool):
                    actual_state = toggle_state
            except Exception as e:
                self.logger.debug(f"get_toggle_state failed for '{target}': {e}")
        
        # Fallback to is_checked
        if actual_state is None and hasattr(element, 'is_checked'):
            try:
                actual_state = bool(element.is_checked())
            except Exception as e:
                self.logger.debug(f"is_checked failed for '{target}': {e}")
        
        if actual_state is None:
            self.logger.error(f"Could not determine checkbox state for '{target}'")
            return False
        
        result = (actual_state == expected)
        
        self.logger.info(
            f"checkbox_state condition: target='{target}', "
            f"state={actual_state}, expected={expected}, result={result}"
        )
        
        return result

    def _resolve_element(self, target: str, required_field: str = ""):
        """
        Resolve an element from a target string formatted as 'module.Class.element'.
        """
        if not target:
            self.logger.error(f"{required_field} condition requires 'target' parameter")
            return None
        
        parts = target.split('.')
        if len(parts) < 3:
            self.logger.error(f"Invalid target format '{target}'. Expected 'module.Class.element'")
            return None
        
        module_name = parts[0]
        class_name = parts[1]
        element_name = parts[2]
        
        try:
            module = importlib.import_module(f"src.pages.{module_name}")
            page_class = getattr(module, class_name)
            page_instance = page_class()
            
            if not hasattr(page_instance, element_name):
                self.logger.error(f"Page '{class_name}' has no element '{element_name}'")
                return None
            
            return getattr(page_instance, element_name)
        
        except ImportError as e:
            self.logger.error(f"Could not import page module 'src.pages.{module_name}': {e}")
        except AttributeError as e:
            self.logger.error(f"Attribute error resolving target '{target}': {e}")
        except Exception as e:
            self.logger.error(f"Error resolving target '{target}': {e}")
        
        return None
