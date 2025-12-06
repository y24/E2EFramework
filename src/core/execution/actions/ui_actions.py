import importlib
from typing import Dict, Any
from src.core.execution.actions.base_action import BaseAction
from src.core.execution.actions.action_dispatcher import ActionDispatcher

class UIAction(BaseAction):
    def execute(self, params: Dict[str, Any]):
        operation = params.get('operation')
        target = params.get('target') # e.g. "notepad_page.NotepadPage.editor" or just "NotepadPage.editor" if we have a map
        value = params.get('value')
        
        # Target Resolution Strategy:
        # Expected format: "Module.Class.Element" (e.g., "notepad_page.NotepadPage.editor")
        # Or simpler: "PageName.Element" if we scan pages.
        # For simplicity, let's assume "notepad_page.NotepadPage.editor" for now, 
        # or implement a helper to find the class.
        
        # Let's support "notepad_page.NotepadPage.editor" (Module relative to src.pages . Class . Property)
        
        if not target:
             raise ValueError("Target is required for UIAction")
             
        parts = target.split('.')
        if len(parts) < 3:
            raise ValueError(f"Invalid target format '{target}'. Expected 'module.Class.property'")
            
        module_name = parts[0]
        class_name = parts[1]
        element_name = parts[2]
        
        # Dynamic import
        try:
            module = importlib.import_module(f"src.pages.{module_name}")
            page_class = getattr(module, class_name)
            page_instance = page_class() # Instantiate
            
            # Get the element (WindowSpecification)
            if not hasattr(page_instance, element_name):
                 raise AttributeError(f"Page '{class_name}' has no element '{element_name}'")
                 
            element = getattr(page_instance, element_name)
            
            # Perform Operation
            if operation == 'input':
                # pywinauto set_text or type_keys
                # set_text is faster but might not trigger events. type_keys simulates keystrokes.
                # using type_keys for better compatibility with modern apps
                if value is None: value = ""
                element.type_keys(value, with_spaces=True)
                
            elif operation == 'click':
                element.click_input()
                
            else:
                raise ValueError(f"Unknown UI operation: {operation}")

        except ImportError as e:
            raise ImportError(f"Could not import page module 'src.pages.{module_name}': {e}")
        except Exception as e:
            raise Exception(f"UI Action Failed on {target}: {e}")

# Registration
ActionDispatcher.register('ui', UIAction)
