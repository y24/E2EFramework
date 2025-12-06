import importlib
from typing import Dict, Any
from src.core.execution.actions.base_action import BaseAction
from src.core.execution.actions.action_dispatcher import ActionDispatcher
from src.utils.screenshot import ScreenshotManager

class ScreenshotAction(BaseAction):
    def execute(self, params: Dict[str, Any]):
        filename = params.get('filename')
        target = params.get('target')
        
        manager = ScreenshotManager()
        
        if target:
            # UIAction like target resolution
            try:
                parts = target.split('.')
                if len(parts) >= 3:
                    module_name = parts[0]
                    class_name = parts[1]
                    element_name = parts[2]
                    
                    module = importlib.import_module(f"src.pages.{module_name}")
                    page_class = getattr(module, class_name)
                    # Page classes in this framework seem to be initialized without args
                    page_instance = page_class()
                    
                    if hasattr(page_instance, element_name):
                        element = getattr(page_instance, element_name)
                        # The element needs to be a wrapper that supports capture_as_image
                        # pywinauto elements usually do.
                        manager.capture_element(element, filename)
                        return
                    else:
                        print(f"Warning: Element '{element_name}' not found on page '{class_name}'. Capturing full screen instead.")
                else:
                    print(f"Warning: Invalid target format '{target}'. Expected 'module.Class.Element'. Capturing full screen instead.")
            except Exception as e:
                print(f"Warning: Failed to resolve target '{target}' for screenshot: {e}. Capturing full screen instead.")
                
        # Fallback or default to full screen
        manager.capture_screen(filename)

# Register the action
ActionDispatcher.register('screenshot', ScreenshotAction)
