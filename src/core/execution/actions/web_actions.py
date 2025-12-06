"""
WebAction - Webブラウザ操作用アクションハンドラ

Seleniumを使用したWebブラウザ操作を提供する。
"""
import time
from typing import Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException

from src.core.execution.actions.base_action import BaseAction
from src.core.execution.actions.action_dispatcher import ActionDispatcher
from src.utils.web_driver_factory import WebDriverFactory


class WebAction(BaseAction):
    """Webブラウザ操作アクション"""
    
    DEFAULT_TIMEOUT = 10
    
    def execute(self, params: Dict[str, Any]):
        operation = params.get('operation')
        
        if operation == 'start_browser':
            browser = params.get('browser', 'chrome')
            headless = params.get('headless', False)
            WebDriverFactory.start_browser(browser, headless=headless)
            
        elif operation == 'connect_browser':
            debugger_address = params.get('debugger_address', 'localhost:9222')
            browser = params.get('browser', 'chrome')
            WebDriverFactory.connect_browser(debugger_address, browser)
            
        elif operation == 'navigate':
            url = params.get('url')
            if not url:
                raise ValueError("URL is required for navigate operation")
            WebDriverFactory.navigate(url)
            
        elif operation == 'click':
            target = params.get('target')
            timeout = params.get('timeout', self.DEFAULT_TIMEOUT)
            self._click_element(target, timeout)
            
        elif operation == 'input':
            target = params.get('target')
            value = params.get('value', '')
            clear = params.get('clear', True)
            timeout = params.get('timeout', self.DEFAULT_TIMEOUT)
            self._input_text(target, value, clear, timeout)
            
        elif operation == 'read':
            target = params.get('target')
            save_as = params.get('save_as')
            timeout = params.get('timeout', self.DEFAULT_TIMEOUT)
            text = self._read_text(target, timeout)
            if save_as:
                self.context.set_variable(save_as, text)
                
        elif operation == 'accept_alert':
            timeout = params.get('timeout', self.DEFAULT_TIMEOUT)
            self._handle_alert(accept=True, timeout=timeout)
            
        elif operation == 'dismiss_alert':
            timeout = params.get('timeout', self.DEFAULT_TIMEOUT)
            self._handle_alert(accept=False, timeout=timeout)
            
        elif operation == 'wait':
            duration = float(params.get('duration', 1.0))
            time.sleep(duration)
            
        elif operation == 'close_browser':
            WebDriverFactory.close_browser()
            
        else:
            raise ValueError(f"Unknown web operation: {operation}")
    
    def _resolve_target(self, target: str):
        """
        ターゲット指定を解決してSelenium要素を取得
        
        ターゲット形式:
        - ページオブジェクト: "alert_sample_page.AlertSamplePage.alert_button"
        - 直接指定 (xpath): "xpath://button[@id='submit']"
        - 直接指定 (css): "css:#submit"
        - 直接指定 (id): "id:submit"
        """
        if not target:
            raise ValueError("Target is required")
        
        # 直接ロケーター指定
        if ':' in target and not target.count('.') >= 2:
            locator_type, locator_value = target.split(':', 1)
            return self._get_by_type(locator_type), locator_value
        
        # ページオブジェクト形式: "module.Class.element"
        import importlib
        parts = target.split('.')
        if len(parts) < 3:
            raise ValueError(f"Invalid target format '{target}'. Expected 'module.Class.property' or 'locator_type:value'")
        
        module_name = parts[0]
        class_name = parts[1]
        element_name = parts[2]
        
        try:
            module = importlib.import_module(f"src.pages.{module_name}")
            page_class = getattr(module, class_name)
            page_instance = page_class()
            
            if not hasattr(page_instance, element_name):
                raise AttributeError(f"Page '{class_name}' has no element '{element_name}'")
            
            locator = getattr(page_instance, element_name)
            # ロケーターは (by_type, value) のタプル形式を想定
            if isinstance(locator, tuple) and len(locator) == 2:
                return self._get_by_type(locator[0]), locator[1]
            else:
                raise ValueError(f"Invalid locator format for '{element_name}': expected (type, value) tuple")
                
        except ImportError as e:
            raise ImportError(f"Could not import page module 'src.pages.{module_name}': {e}")
    
    def _get_by_type(self, locator_type: str) -> By:
        """ロケータータイプをSelenium Byに変換"""
        mapping = {
            'xpath': By.XPATH,
            'css': By.CSS_SELECTOR,
            'id': By.ID,
            'name': By.NAME,
            'class': By.CLASS_NAME,
            'tag': By.TAG_NAME,
            'link_text': By.LINK_TEXT,
            'partial_link_text': By.PARTIAL_LINK_TEXT,
        }
        locator_type = locator_type.lower()
        if locator_type not in mapping:
            raise ValueError(f"Unknown locator type: {locator_type}")
        return mapping[locator_type]
    
    def _find_element(self, target: str, timeout: int):
        """要素を待機して取得"""
        driver = WebDriverFactory.get_driver()
        by, value = self._resolve_target(target)
        
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.presence_of_element_located((by, value)))
        return element
    
    def _click_element(self, target: str, timeout: int):
        """要素をクリック"""
        driver = WebDriverFactory.get_driver()
        by, value = self._resolve_target(target)
        
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.element_to_be_clickable((by, value)))
        element.click()
    
    def _input_text(self, target: str, value: str, clear: bool, timeout: int):
        """テキストを入力"""
        element = self._find_element(target, timeout)
        if clear:
            element.clear()
        element.send_keys(value)
    
    def _read_text(self, target: str, timeout: int) -> str:
        """テキストを取得"""
        element = self._find_element(target, timeout)
        # inputやtextareaの場合はvalueを取得
        tag_name = element.tag_name.lower()
        if tag_name in ('input', 'textarea'):
            return element.get_attribute('value') or ''
        return element.text
    
    def _handle_alert(self, accept: bool, timeout: int):
        """アラートを処理"""
        driver = WebDriverFactory.get_driver()
        wait = WebDriverWait(driver, timeout)
        
        try:
            alert = wait.until(EC.alert_is_present())
            if accept:
                alert.accept()
            else:
                alert.dismiss()
        except TimeoutException:
            raise TimeoutException(f"No alert present after {timeout} seconds")


# ActionDispatcherに登録
ActionDispatcher.register('web', WebAction)
