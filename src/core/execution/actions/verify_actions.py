import os
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

        if target:
            try:
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
                
                element = getattr(page_instance, element_name)
                
                if check_type == 'exists':
                    if not element.exists():
                         raise AssertionError(f"Element '{target}' not found")
                    return

                # Try to get text for other checks
                try:
                    actual_value = element.get_value()
                except:
                    actual_value = element.window_text()

            except Exception as e:
                raise Exception(f"Failed to resolve verification target '{target}': {e}")
        
        if check_type == 'equals':
            expected = params.get('expected')
            assert actual_value == expected, f"Verification failed: expected '{expected}', but got '{actual_value}'"
            
        elif check_type == 'file_exists':
            path = params.get('path')
            assert os.path.exists(path), f"File does not exist: {path}"
            
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

        elif check_type == 'contains':
            haystack = actual_value if actual_value is not None else params.get('text')
            needle = params.get('contains')
            assert needle in haystack, f"Text '{needle}' not found in '{haystack}'"

        else:
            raise ValueError(f"Unknown verify type: {check_type}")

# Registration
ActionDispatcher.register('verify', VerifyAction)
