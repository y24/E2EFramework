"""
WebDriverFactory - Webブラウザドライバー管理クラス

Seleniumを使用してWebブラウザの起動・接続・終了を管理する。
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Optional
import logging


class WebDriverFactory:
    """Webブラウザドライバーのファクトリークラス"""
    
    _driver: Optional[WebDriver] = None
    _logger = logging.getLogger(__name__)

    @classmethod
    def get_driver(cls) -> WebDriver:
        """現在のWebDriverを取得"""
        if cls._driver is None:
            raise RuntimeError("Browser not started. Call start_browser or connect_browser first.")
        return cls._driver

    @classmethod
    def start_browser(cls, browser_type: str = "chrome", headless: bool = False) -> WebDriver:
        """
        新しいブラウザインスタンスを起動
        
        Args:
            browser_type: ブラウザ種別 ("chrome", "firefox", "edge")
            headless: ヘッドレスモードで起動するか
        
        Returns:
            WebDriver: 起動したブラウザのドライバー
        """
        browser_type = browser_type.lower()
        
        if browser_type == "chrome":
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            cls._driver = webdriver.Chrome(options=options)
            
        elif browser_type == "firefox":
            options = FirefoxOptions()
            if headless:
                options.add_argument("--headless")
            cls._driver = webdriver.Firefox(options=options)
            
        elif browser_type == "edge":
            options = EdgeOptions()
            if headless:
                options.add_argument("--headless=new")
            cls._driver = webdriver.Edge(options=options)
            
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")
        
        cls._logger.info(f"Started {browser_type} browser")
        return cls._driver

    @classmethod
    def connect_browser(cls, debugger_address: str = "localhost:9222", browser_type: str = "chrome") -> WebDriver:
        """
        リモートデバッグで既存のブラウザに接続
        
        事前に以下のようにブラウザを起動しておく必要があります:
        chrome.exe --remote-debugging-port=9222
        
        Args:
            debugger_address: デバッガーアドレス (デフォルト: "localhost:9222")
            browser_type: ブラウザ種別 ("chrome", "firefox", "edge")
        
        Returns:
            WebDriver: 接続したブラウザのドライバー
        """
        browser_type = browser_type.lower()
        
        if browser_type == "chrome":
            options = ChromeOptions()
            options.add_experimental_option("debuggerAddress", debugger_address)
            cls._driver = webdriver.Chrome(options=options)
            
        elif browser_type == "edge":
            options = EdgeOptions()
            options.add_experimental_option("debuggerAddress", debugger_address)
            cls._driver = webdriver.Edge(options=options)
            
        elif browser_type == "firefox":
            # Firefoxはリモートデバッグの設定が異なる
            raise NotImplementedError("Firefox remote debugging is not supported yet")
            
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")
        
        cls._logger.info(f"Connected to existing {browser_type} browser at {debugger_address}")
        return cls._driver

    @classmethod
    def navigate(cls, url: str) -> None:
        """指定URLに遷移"""
        driver = cls.get_driver()
        driver.get(url)
        cls._logger.info(f"Navigated to: {url}")

    @classmethod
    def close_browser(cls) -> None:
        """ブラウザを終了"""
        if cls._driver:
            try:
                cls._driver.quit()
                cls._logger.info("Browser closed")
            except Exception as e:
                cls._logger.warning(f"Error closing browser: {e}")
            finally:
                cls._driver = None

    @classmethod
    def is_active(cls) -> bool:
        """ブラウザがアクティブかどうかを確認"""
        return cls._driver is not None
