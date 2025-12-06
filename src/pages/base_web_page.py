"""
BaseWebPage - Webページオブジェクト用基底クラス

Seleniumを使用したWebページ要素の定義・取得を提供する。
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from typing import Tuple, Optional

from src.utils.web_driver_factory import WebDriverFactory


class BaseWebPage:
    """Webページオブジェクトの基底クラス"""
    
    DEFAULT_TIMEOUT = 10
    
    def __init__(self):
        """BaseWebPageの初期化"""
        pass
    
    @property
    def driver(self):
        """現在のWebDriverを取得"""
        return WebDriverFactory.get_driver()
    
    def find_element(self, locator: Tuple[str, str], timeout: int = None) -> WebElement:
        """
        要素を待機して取得
        
        Args:
            locator: (ロケータータイプ, 値) のタプル
            timeout: タイムアウト秒数
        
        Returns:
            WebElement: 見つかった要素
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        by = self._get_by_type(locator[0])
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located((by, locator[1])))
    
    def find_elements(self, locator: Tuple[str, str], timeout: int = None) -> list:
        """複数要素を待機して取得"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        by = self._get_by_type(locator[0])
        wait = WebDriverWait(self.driver, timeout)
        wait.until(EC.presence_of_element_located((by, locator[1])))
        return self.driver.find_elements(by, locator[1])
    
    def wait_for_element(self, locator: Tuple[str, str], timeout: int = None) -> bool:
        """要素が表示されるまで待機"""
        try:
            self.find_element(locator, timeout)
            return True
        except:
            return False
    
    def element_exists(self, locator: Tuple[str, str]) -> bool:
        """要素が存在するかチェック（待機なし）"""
        by = self._get_by_type(locator[0])
        elements = self.driver.find_elements(by, locator[1])
        return len(elements) > 0
    
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
