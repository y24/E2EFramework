import os
import time
import winreg
import logging
from pywinauto import Application, Desktop
from pywinauto.findwindows import find_window
from typing import Optional

logger = logging.getLogger(__name__)


def get_excel_path():
    """レジストリからExcelのインストールパスを取得"""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe") as key:
            path, _ = winreg.QueryValueEx(key, "")
            if os.path.exists(path):
                return path
    except Exception:
        pass

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Office\16.0\Excel\InstallRoot") as key:
            path, _ = winreg.QueryValueEx(key, "Path")
            excel_path = os.path.join(path, "EXCEL.EXE")
            if os.path.exists(excel_path):
                return excel_path
    except Exception:
        pass

    # フォールバック: 一般的なパスを試す
    fallback_paths = [
        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files\Microsoft Office\Office16\EXCEL.EXE",
    ]
    for path in fallback_paths:
        if os.path.exists(path):
            return path

    return None


class DriverFactory:
    """アプリケーション管理のファクトリクラス"""
    
    # 汎用アプリケーション用
    _app: Optional[Application] = None
    _backend: str = "uia"
    
    # Excel専用
    _excel_app: Optional[Application] = None
    _excel_window = None
    _excel_backend: str = "uia"

    # ========== 汎用アプリケーション管理 ==========
    
    @classmethod
    def get_app(cls) -> Application:
        if cls._app is None:
            raise RuntimeError("Application not started. Call start_app or connect_app first.")
        return cls._app

    @classmethod
    def start_app(cls, path: str, backend: str = "uia", timeout: int = 10):
        cls._backend = backend
        cls._app = Application(backend=backend).start(path, timeout=timeout)
        time.sleep(1)
        return cls._app

    @classmethod
    def connect_app(cls, **kwargs):
        """
        Connect to an existing application. 
        kwargs can be path, title, handle, etc.
        """
        backend = kwargs.pop('backend', 'uia')
        cls._backend = backend
        cls._app = Application(backend=backend).connect(**kwargs)
        return cls._app

    @classmethod
    def close_app(cls):
        if cls._app:
            try:
                cls._app.kill()
            except Exception:
                pass
            cls._app = None

    # ========== Excel専用管理 ==========
    
    @classmethod
    def start_excel(cls, file_path: str = None, timeout: int = 10):
        """
        Excelを起動してファイルを開く
        
        Args:
            file_path: 開くファイルのパス（省略可）
            timeout: 起動タイムアウト（秒）
        
        Returns:
            Application: 起動したExcelアプリケーション
        """
        excel_path = get_excel_path()
        if excel_path is None:
            raise RuntimeError("Excelが見つかりません。Excelがインストールされているか確認してください。")
        
        logger.info(f"Excelを起動中: {excel_path}")
        
        if file_path and os.path.exists(file_path):
            cmd = f'"{excel_path}" "{file_path}" /e'
            cls._excel_app = Application(backend='uia').start(cmd, timeout=timeout)
            logger.info(f"Excelファイルを開きました: {file_path}")
        else:
            cls._excel_app = Application(backend='uia').start(excel_path, timeout=timeout)
            logger.info("新しいExcelを起動しました")
        
        # ウィンドウを待機・取得
        cls._excel_window = cls._wait_for_excel_window()
        
        return cls._excel_app
    
    @classmethod
    def _wait_for_excel_window(cls, timeout: float = 10, check_interval: float = 0.5):
        """Excelウィンドウが表示されるまで待機"""
        logger.info(f"Excelウィンドウの表示を待機中... (タイムアウト: {timeout}秒)")
        
        elapsed_time = 0
        while elapsed_time < timeout:
            try:
                window_handle = find_window(process='EXCEL.EXE')
                if window_handle:
                    excel_window = cls._excel_app.window(handle=window_handle)
                    if excel_window.is_visible():
                        logger.info(f"Excelウィンドウを検出しました（{elapsed_time:.1f}秒後）")
                        return excel_window
            except Exception as e:
                logger.debug(f"ウィンドウ検索中（{elapsed_time:.1f}秒）: {e}")
            
            time.sleep(check_interval)
            elapsed_time += check_interval
        
        # フォールバック: タイトルパターンで検索
        try:
            excel_window = cls._excel_app.window(title_re=r'.*Excel.*')
            excel_window.wait('visible', timeout=5)
            logger.info("タイトルパターンでExcelウィンドウを検出しました")
            return excel_window
        except Exception as e:
            logger.error(f"Excelウィンドウの検出に失敗: {e}")
            raise RuntimeError("Excelウィンドウを検出できませんでした")
    
    @classmethod
    def get_excel_app(cls) -> Application:
        """Excel Applicationを取得"""
        if cls._excel_app is None:
            raise RuntimeError("Excel not started. Call start_excel first.")
        return cls._excel_app
    
    @classmethod
    def get_excel_window(cls):
        """Excelウィンドウを取得"""
        if cls._excel_window is None:
            raise RuntimeError("Excel window not available. Call start_excel first.")
        return cls._excel_window
    
    @classmethod
    def is_excel_running(cls) -> bool:
        """Excelが起動中かどうか"""
        if cls._excel_app is None:
            return False
        try:
            return cls._excel_app.is_process_running()
        except:
            return False
    
    @classmethod
    def close_excel(cls):
        """Excelを終了"""
        if cls._excel_app:
            try:
                if cls._excel_app.is_process_running():
                    cls._excel_app.kill()
                    logger.info("Excelを終了しました")
            except Exception as e:
                logger.debug(f"Excel終了エラー（無視可能）: {e}")
            finally:
                cls._excel_app = None
                cls._excel_window = None
    
    # ========== 全アプリケーション管理 ==========
    
    @classmethod
    def close_all(cls):
        """すべてのアプリケーションを終了"""
        cls.close_app()
        cls.close_excel()
