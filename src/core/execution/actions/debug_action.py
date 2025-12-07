"""
Debug Action for E2E Framework

Provides debugging utilities for UI automation development:
- List all desktop windows
- List descendants of a page object
- Check for specific dialog classes
"""
import importlib
import logging
from typing import Dict, Any, List
from pywinauto import Desktop
from src.core.execution.actions.base_action import BaseAction
from src.core.execution.actions.action_dispatcher import ActionDispatcher


class DebugAction(BaseAction):
    """
    Debug action for development and troubleshooting.
    
    Supported actions:
    - list_desktop_windows: List all top-level desktop windows
    - list_descendants: List all descendants of a page element
    - check_dialog: Check if a dialog with specific class exists
    """
    
    def __init__(self, context):
        super().__init__(context)
        self.logger = logging.getLogger(__name__)
    
    def execute(self, params: Dict[str, Any]):
        action = params.get('action')
        
        if action == 'list_desktop_windows':
            self._list_desktop_windows(params)
        
        elif action == 'list_descendants':
            self._list_descendants(params)
        
        elif action == 'check_dialog':
            self._check_dialog(params)
        
        else:
            raise ValueError(f"Unknown debug action: {action}")
    
    def _list_desktop_windows(self, params: Dict[str, Any]):
        """
        List all top-level windows on the desktop.
        
        Params:
            filter (str, optional): Filter windows by title (partial match)
            control_type (str, optional): Filter by control type
        """
        title_filter = params.get('filter', '')
        control_type_filter = params.get('control_type', '')
        
        self.logger.info("=== Desktop Windows ===")
        print("\n=== Desktop Windows ===")
        
        desktop = Desktop(backend='uia')
        windows = desktop.windows()
        
        for w in windows:
            try:
                title = w.window_text()
                control_type = w.element_info.control_type
                class_name = w.element_info.class_name
                
                # Apply filters
                if title_filter and title_filter.lower() not in title.lower():
                    continue
                if control_type_filter and control_type_filter != control_type:
                    continue
                
                if title:  # Only show windows with titles
                    msg = f"  [{title}] control_type={control_type}, class={class_name}"
                    self.logger.info(msg)
                    print(msg)
            except Exception as e:
                self.logger.debug(f"Error reading window: {e}")
        
        print("=== End Desktop Windows ===\n")
        self.logger.info("=== End Desktop Windows ===")
    
    def _list_descendants(self, params: Dict[str, Any]):
        """
        List all descendants of a page element.
        
        Params:
            target (str): Page object path (e.g., "notepad_page.NotepadPage" or "notepad_page.NotepadPage.window")
            filter (str, optional): Filter elements by text (partial match)
            control_type (str, optional): Filter by control type
            depth (int, optional): Maximum depth to traverse (default: unlimited)
        """
        target = params.get('target')
        text_filter = params.get('filter', '')
        control_type_filter = params.get('control_type', '')
        max_depth = params.get('depth', None)
        
        if not target:
            raise ValueError("'target' is required for list_descendants action")
        
        # Parse target: "module.Class" or "module.Class.property"
        parts = target.split('.')
        if len(parts) < 2:
            raise ValueError(f"Invalid target format '{target}'. Expected 'module.Class' or 'module.Class.property'")
        
        module_name = parts[0]
        class_name = parts[1]
        property_name = parts[2] if len(parts) >= 3 else 'window'
        
        try:
            # Dynamic import
            module = importlib.import_module(f"src.pages.{module_name}")
            page_class = getattr(module, class_name)
            page_instance = page_class()
            
            # Get the element
            element = getattr(page_instance, property_name)
            
            self.logger.info(f"=== Descendants of {target} ===")
            print(f"\n=== Descendants of {target} ===")
            
            # Get wrapper and list descendants
            try:
                wrapper = element.wrapper_object()
                descendants = wrapper.descendants()
                
                count = 0
                for desc in descendants:
                    try:
                        text = desc.window_text()
                        control_type = desc.element_info.control_type
                        class_name_elem = desc.element_info.class_name
                        
                        # Apply filters
                        if text_filter and text_filter.lower() not in text.lower():
                            continue
                        if control_type_filter and control_type_filter != control_type:
                            continue
                        
                        msg = f"  [{text}] control_type={control_type}, class={class_name_elem}"
                        self.logger.info(msg)
                        print(msg)
                        count += 1
                        
                        if max_depth and count >= max_depth:
                            print(f"  ... (showing first {max_depth} elements)")
                            break
                            
                    except Exception as e:
                        self.logger.debug(f"Error reading descendant: {e}")
                
                summary = f"Total: {len(descendants)} elements" + (f" (filtered to {count})" if text_filter or control_type_filter else "")
                print(summary)
                self.logger.info(summary)
                
            except Exception as e:
                error_msg = f"Error getting descendants: {e}"
                self.logger.error(error_msg)
                print(error_msg)
            
            print(f"=== End Descendants ===\n")
            self.logger.info("=== End Descendants ===")
            
        except ImportError as e:
            raise ImportError(f"Could not import page module 'src.pages.{module_name}': {e}")
        except AttributeError as e:
            raise AttributeError(f"Could not find '{property_name}' on '{class_name}': {e}")
    
    def _check_dialog(self, params: Dict[str, Any]):
        """
        Check if a dialog with specific class or title exists.
        
        Params:
            class_name (str, optional): Dialog class name (e.g., "#32770")
            title (str, optional): Dialog title (partial match)
            timeout (float, optional): Timeout in seconds (default: 1)
        """
        class_name = params.get('class_name')
        title = params.get('title')
        timeout = float(params.get('timeout', 1))
        
        if not class_name and not title:
            raise ValueError("Either 'class_name' or 'title' is required for check_dialog action")
        
        self.logger.info("=== Dialog Check ===")
        print("\n=== Dialog Check ===")
        
        desktop = Desktop(backend='uia')
        
        try:
            # Build search criteria
            criteria = {}
            if class_name:
                criteria['class_name'] = class_name
            if title:
                criteria['title_re'] = f".*{title}.*"
            
            dialog = desktop.window(**criteria)
            exists = dialog.exists(timeout=timeout)
            
            if exists:
                wrapper = dialog.wrapper_object()
                actual_title = wrapper.window_text()
                actual_class = wrapper.element_info.class_name
                actual_control_type = wrapper.element_info.control_type
                
                msg = f"  [OK] Dialog FOUND: [{actual_title}] class={actual_class}, control_type={actual_control_type}"
                self.logger.info(msg)
                print(msg)
            else:
                criteria_str = ", ".join(f"{k}={v}" for k, v in criteria.items())
                msg = f"  [NG] Dialog NOT FOUND: {criteria_str}"
                self.logger.info(msg)
                print(msg)
                
        except Exception as e:
            error_msg = f"  [WARN] Error checking dialog: {e}"
            self.logger.error(error_msg)
            print(error_msg)
        
        print("=== End Dialog Check ===\n")
        self.logger.info("=== End Dialog Check ===")


# Registration
ActionDispatcher.register('debug', DebugAction)
