import os
import re
import importlib
from typing import Dict, Any
from src.core.execution.actions.base_action import BaseAction
from src.core.execution.actions.action_dispatcher import ActionDispatcher
from src.utils.file_validator import FileValidator

class VerifyAction(BaseAction):
    def execute(self, params: Dict[str, Any]):
        check_type = params.get('type')
        
        # Resolve target if specified
        target = params.get('target')
        actual_value = params.get('actual')
        element = None

        if target:
            try:
                element = self._resolve_target(target)
            except Exception as e:
                raise Exception(f"Failed to resolve verification target '{target}': {e}")

            if check_type == 'exists':
                if not element.exists():
                    raise AssertionError(f"Element '{target}' not found")
                return

            if check_type == 'not_exists':
                if element.exists():
                    raise AssertionError(f"Element '{target}' unexpectedly exists")
                return

            if check_type == 'clickable':
                self._assert_clickable(element, target)
                return

            if actual_value is None:
                actual_value = self._get_element_text(element)

        if check_type in ['exists', 'not_exists', 'clickable'] and not target:
            raise ValueError(f"'target' is required for {check_type} verification")
        
        if check_type == 'equals':
            expected = params.get('expected')
            if actual_value != expected:
                raise AssertionError(f"Verification failed: expected '{expected}', but got '{actual_value}'")

        elif check_type == 'contains':
            haystack = actual_value if actual_value is not None else params.get('text')
            needle = params.get('contains')
            use_regex = params.get('regex', False)

            if isinstance(use_regex, str):
                use_regex = use_regex.lower() == 'true'

            if haystack is None:
                raise AssertionError("No text available for 'contains' verification")
            if needle is None:
                raise ValueError("'contains' parameter is required for contains verification")

            haystack_str = str(haystack)
            if use_regex:
                if re.search(needle, haystack_str) is None:
                    raise AssertionError(f"Regex '{needle}' not found in '{haystack_str}'")
            else:
                if needle not in haystack_str:
                    raise AssertionError(f"Text '{needle}' not found in '{haystack_str}'")

        elif check_type == 'not_contains':
            haystack = actual_value if actual_value is not None else params.get('text')
            needle = params.get('not_contains') or params.get('contains')
            use_regex = params.get('regex', False)

            if isinstance(use_regex, str):
                use_regex = use_regex.lower() == 'true'

            if haystack is None:
                raise AssertionError("No text available for 'not_contains' verification")
            if needle is None:
                raise ValueError("'not_contains' (or 'contains') parameter is required for not_contains verification")

            haystack_str = str(haystack)
            if use_regex:
                if re.search(needle, haystack_str):
                    raise AssertionError(f"Regex '{needle}' unexpectedly matched '{haystack_str}'")
            else:
                if needle in haystack_str:
                    raise AssertionError(f"Text '{needle}' unexpectedly found in '{haystack_str}'")

        elif check_type == 'matches':
            pattern = params.get('pattern') or params.get('regex')
            if pattern is None:
                raise ValueError("'pattern' parameter is required for matches verification")

            target_text = actual_value if actual_value is not None else params.get('text')
            if target_text is None:
                raise AssertionError("No text available for 'matches' verification")

            if re.fullmatch(pattern, str(target_text)) is None:
                raise AssertionError(f"Text '{target_text}' does not match pattern '{pattern}'")

        elif check_type == 'file_exists':
            path = params.get('path')
            if not os.path.exists(path):
                raise AssertionError(f"File does not exist: {path}")
            
            min_size = params.get('min_size')
            if min_size is not None:
                actual_size = os.path.getsize(path)
                if actual_size < int(min_size):
                    raise AssertionError(f"File size {actual_size} bytes is smaller than required {min_size} bytes")

        elif check_type == 'file_content':
            path = params.get('path')
            file_type = params.get('file_type')
            
            # Infer file type if not provided
            if not file_type:
                if path.lower().endswith('.xlsx') or path.lower().endswith('.xls'):
                    file_type = 'excel'
                else:
                    file_type = 'text'

            if file_type == 'text':
                FileValidator.validate_text_file(
                    path=path,
                    expected_content=params.get('expected'),
                    mode=params.get('mode', 'exact'),
                    encoding=params.get('encoding', 'utf-8')
                )
            elif file_type == 'excel':
                FileValidator.validate_excel_file(
                    path=path,
                    cell=params.get('cell'),
                    expected_value=params.get('expected'),
                    sheet_name=params.get('sheet')
                )
            else:
                raise ValueError(f"Unsupported file_type for file_content verification: {file_type}")

        else:
            raise ValueError(f"Unknown verify type: {check_type}")

    def _resolve_target(self, target: str):
        parts = target.split('.')
        if len(parts) < 3:
            raise ValueError(f"Invalid target format '{target}'. Expected 'module.Class.property'")
        
        module_name = parts[0]
        class_name = parts[1]
        element_name = parts[2]
        
        module = importlib.import_module(f"src.pages.{module_name}")
        page_class = getattr(module, class_name)
        page_instance = page_class()
        
        if not hasattr(page_instance, element_name):
            raise AttributeError(f"Page '{class_name}' has no element '{element_name}'")
        
        return getattr(page_instance, element_name)

    def _get_element_text(self, element):
        try:
            return element.get_value()
        except Exception:
            try:
                return element.window_text()
            except Exception:
                return None

    def _assert_clickable(self, element, target: str):
        try:
            exists = element.exists()
        except Exception as e:
            raise AssertionError(f"Failed to check existence for '{target}': {e}")

        if not exists:
            raise AssertionError(f"Element '{target}' not found for clickable verification")

        try:
            is_enabled = element.is_enabled()
        except Exception as e:
            raise AssertionError(f"Failed to check enabled state for '{target}': {e}")

        is_visible = True
        if hasattr(element, 'is_visible'):
            try:
                is_visible = element.is_visible()
            except Exception:
                is_visible = True  # If visibility cannot be determined, do not fail solely on that.

        if not (is_enabled and is_visible):
            raise AssertionError(f"Element '{target}' not clickable: enabled={is_enabled}, visible={is_visible}")

# Registration
ActionDispatcher.register('verify', VerifyAction)
