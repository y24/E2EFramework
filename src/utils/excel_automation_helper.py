#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel UI自動化ヘルパークラス
pywinautoを使用してExcelのUI操作を自動化

DriverFactoryと連携してアプリケーション管理を行う
"""

import time
import os
import logging
from pywinauto.keyboard import send_keys

from src.utils.excel_automation_configs import ExcelConfig

logger = logging.getLogger(__name__)


class ExcelAutomationHelper:
    """Excel UI自動化のヘルパークラス"""
    
    def __init__(self):
        # DriverFactoryから取得（遅延バインディング）
        self._app = None
        self._excel_window = None
        self.copied_files = []  # コピーしたファイルのパスを記録

    @property
    def app(self):
        """Application を取得（DriverFactory経由）"""
        if self._app is None:
            from src.utils.driver_factory import DriverFactory
            if DriverFactory.is_excel_running():
                self._app = DriverFactory.get_excel_app()
        return self._app
    
    @app.setter
    def app(self, value):
        self._app = value

    @property
    def excel_window(self):
        """Excelウィンドウを取得（DriverFactory経由）"""
        if self._excel_window is None:
            from src.utils.driver_factory import DriverFactory
            if DriverFactory.is_excel_running():
                self._excel_window = DriverFactory.get_excel_window()
        return self._excel_window
    
    @excel_window.setter
    def excel_window(self, value):
        self._excel_window = value

    def start_excel(self, file_path=None):
        """Excelを起動し、指定されたファイルを開く"""
        try:
            # 起動前に復旧ファイルを削除
            self._cleanup_recovery_files()

            # DriverFactory経由で起動
            from src.utils.driver_factory import DriverFactory
            DriverFactory.start_excel(file_path)
            
            # 内部キャッシュを更新
            self._app = DriverFactory.get_excel_app()
            self._excel_window = DriverFactory.get_excel_window()

            logger.info("Excelウィンドウの準備が完了しました")
            return True

        except Exception as e:
            logger.error(f"Excel起動エラー: {e}")
            import traceback
            traceback.print_exc()
            return False

    def activate_excel_window(self, max_retries=3, retry_delay=1.0):
        """
        Excelウィンドウをアクティベートする

        Args:
            max_retries (int): 最大リトライ回数
            retry_delay (float): リトライ間隔（秒）

        Returns:
            bool: アクティベートに成功したかどうか
        """
        try:
            if not self.app or not self.excel_window:
                logger.warning("Excelアプリケーションまたはウィンドウが初期化されていません")
                return False

            for attempt in range(max_retries):
                try:
                    logger.info(f"Excelウィンドウのアクティベートを試行中... (試行 {attempt + 1}/{max_retries})")

                    # pywinautoのset_focus()を使用
                    try:
                        self.excel_window.set_focus()
                        time.sleep(ExcelConfig.get_timing('window_activation'))
                        logger.info("pywinautoのset_focus()でExcelウィンドウをアクティベートしました")
                        return True
                    except Exception as e:
                        logger.debug(f"set_focus()でのアクティベートに失敗: {e}")

                    # win32guiを使用してアクティベート
                    try:
                        import win32gui
                        import win32con

                        hwnd = self.excel_window.handle
                        if hwnd:
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            time.sleep(ExcelConfig.get_timing('window_activation'))
                            win32gui.SetForegroundWindow(hwnd)
                            time.sleep(ExcelConfig.get_timing('window_activation'))
                            logger.info("win32guiを使用してExcelウィンドウをアクティベートしました")
                            return True
                    except Exception as e:
                        logger.debug(f"win32guiでのアクティベートに失敗: {e}")

                    if attempt < max_retries - 1:
                        logger.info(f"アクティベートに失敗しました。{retry_delay}秒後にリトライします...")
                        time.sleep(retry_delay)

                except Exception as e:
                    logger.debug(f"アクティベート試行 {attempt + 1} でエラー: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)

            logger.warning(f"Excelウィンドウのアクティベートに失敗しました（{max_retries}回試行）")
            return False

        except Exception as e:
            logger.error(f"Excelウィンドウアクティベートエラー: {e}")
            return False

    def ensure_excel_active(self, operation_name="操作"):
        """
        操作前にExcelウィンドウがアクティブであることを保証するヘルパーメソッド

        Args:
            operation_name (str): 実行する操作の名前（ログ用）

        Returns:
            bool: Excelウィンドウがアクティブになったかどうか
        """
        try:
            logger.info(f"{operation_name}の前にExcelウィンドウをアクティベート中...")
            if self.activate_excel_window():
                logger.info(f"{operation_name}の準備が完了しました")
                return True
            else:
                logger.warning(f"{operation_name}の準備に失敗しましたが、操作を続行します")
                return False
        except Exception as e:
            logger.error(f"Excelウィンドウアクティベート確認エラー: {e}")
            return False

    def select_cell(self, row=None, column=None, cell_address=None):
        """
        セルを選択
        
        Args:
            row: 行番号（0始まり）
            column: 列番号（0始まり）
            cell_address: セルアドレス（例: "A1"）- row/columnより優先
        """
        try:
            self.ensure_excel_active("セル選択")

            if cell_address:
                address = cell_address.upper()
            else:
                address = ExcelConfig.get_cell_address(row, column)
            
            # Ctrl+G でジャンプ
            send_keys(ExcelConfig.get_shortcut('go_to'))
            time.sleep(ExcelConfig.get_timing('cell_selection'))
            send_keys(address)
            time.sleep(ExcelConfig.get_timing('cell_selection'))
            send_keys('{ENTER}')
            time.sleep(ExcelConfig.get_timing('cell_selection'))
            # ジャンプダイアログを閉じる
            send_keys('{ESC}')
            time.sleep(ExcelConfig.get_timing('cell_selection'))

            logger.info(f"セル {address} を選択しました")
            return True

        except Exception as e:
            logger.error(f"セル選択エラー: {e}")
            return False

    def input_text(self, text):
        """テキストを入力"""
        try:
            self.ensure_excel_active("テキスト入力")

            send_keys(text, with_spaces=True)
            time.sleep(ExcelConfig.get_timing('text_input'))
            send_keys('{ENTER}')
            logger.info(f"テキストを入力しました: {text}")
            return True

        except Exception as e:
            logger.error(f"テキスト入力エラー: {e}")
            return False

    def click_ribbon_shortcut(self, shortcut_key):
        """
        短縮キー形式でリボン操作を実行
        
        Args:
            shortcut_key: 短縮キー（例: "H>AC" でホームタブの中央揃え、"A" でデータタブ表示）
        """
        try:
            self.ensure_excel_active("リボン操作")

            # Altキーでリボンにアクセス
            send_keys('%')
            time.sleep(ExcelConfig.get_timing('text_input'))

            # 短縮キーの形式を解析
            if '>' in shortcut_key:
                parts = [part.strip().upper() for part in shortcut_key.split('>')]

                # 各段階の短縮キーを順次送信
                for key in parts:
                    send_keys(key)
                    time.sleep(ExcelConfig.get_timing('ribbon_operation'))

                logger.info(f"リボン短縮キー '{shortcut_key}' を実行しました")
                return True
            else:
                # タブのみの短縮キーの場合
                send_keys(shortcut_key.upper())
                time.sleep(ExcelConfig.get_timing('ribbon_operation'))
                logger.info(f"リボンタブ短縮キー '{shortcut_key}' を実行しました")
                return True

        except Exception as e:
            logger.error(f"リボン短縮キー実行エラー: {e}")
            return False

    def save_file(self, file_path=None):
        """ファイルを保存"""
        try:
            self.ensure_excel_active("ファイル保存")

            if file_path:
                send_keys(ExcelConfig.get_shortcut('save_as'))
                time.sleep(ExcelConfig.get_timing('file_operation'))
                send_keys(file_path)
                time.sleep(ExcelConfig.get_timing('text_input'))
                send_keys('{ENTER}')
            else:
                send_keys(ExcelConfig.get_shortcut('save_file'))

            time.sleep(ExcelConfig.get_timing('file_operation'))
            logger.info("ファイルを保存しました")
            return True

        except Exception as e:
            logger.error(f"ファイル保存エラー: {e}")
            return False

    def close_workbook(self, save=False):
        """
        ワークブックを閉じる
        
        Args:
            save: 保存するかどうか
        """
        try:
            if self.app:
                self.ensure_excel_active("ワークブックを閉じる")

                # Ctrl+W でワークブックを閉じる
                send_keys(ExcelConfig.get_shortcut('close_workbook'))
                time.sleep(ExcelConfig.get_timing('file_operation'))
                
                # 保存確認ダイアログが表示された場合の処理
                if save:
                    send_keys('{ENTER}')
                else:
                    send_keys('n')
                
                time.sleep(ExcelConfig.get_timing('dialog_wait'))
                logger.info("ワークブックを閉じました")

            return True

        except Exception as e:
            logger.error(f"ワークブックを閉じるエラー: {e}")
            self.exit_excel()
            self._cleanup_recovery_files()
            return False

    def exit_excel(self):
        """Excelを終了する"""
        try:
            from src.utils.driver_factory import DriverFactory
            DriverFactory.close_excel()
            
            # 内部キャッシュをクリア
            self._app = None
            self._excel_window = None
            
            logger.info("Excelを終了しました")
        except Exception as e:
            logger.debug(f"Excel終了エラー（無視可能）: {e}")
        
        self._cleanup_recovery_files()

    def handle_dialog(self, title_patterns, key_action='{ESC}', timeout=10):
        """
        ダイアログを処理する

        Args:
            title_patterns (str or list): ダイアログタイトルのパターン
            key_action (str): 実行するキー操作
            timeout (float): ダイアログ表示待機時間（秒）

        Returns:
            bool: 処理が成功したかどうか
        """
        try:
            from pywinauto.findwindows import find_window
            
            if isinstance(title_patterns, str):
                title_patterns = [title_patterns]

            logger.info(f"ダイアログの表示を待機中... (タイムアウト: {timeout}秒, パターン: {title_patterns})")

            start_time = time.time()
            dialog_found = False
            dialog_window = None
            
            while time.time() - start_time < timeout:
                try:
                    for pattern in title_patterns:
                        try:
                            dialog_window = find_window(title_re=f".*{pattern}.*")
                            if dialog_window:
                                logger.info(f"ダイアログを検出しました: {pattern}")
                                dialog_found = True
                                break
                        except Exception:
                            continue
                    
                    if dialog_found:
                        break
                    
                    time.sleep(0.5)
                except Exception as e:
                    logger.debug(f"ダイアログ待機中のエラー: {e}")
                    time.sleep(0.5)

            if not dialog_found:
                logger.info(f"ダイアログは表示されませんでした (パターン: {title_patterns})")
                return True

            logger.info(f"ダイアログでアクション '{key_action}' を実行")
            time.sleep(ExcelConfig.get_timing('dialog_wait'))
            send_keys(key_action)
            time.sleep(ExcelConfig.get_timing('dialog_wait', 0.2))
            
            logger.info("ダイアログの処理が完了しました")
            return True

        except Exception as e:
            logger.error(f"ダイアログ処理エラー: {e}")
            return False

    def _cleanup_recovery_files(self):
        """復旧ファイルを削除"""
        try:
            import glob
            
            recovery_paths = [
                os.path.expanduser("~/AppData/Local/Microsoft/Office/UnsavedFiles"),
                os.path.expanduser("~/AppData/Roaming/Microsoft/Excel"),
            ]

            recovery_patterns = [
                "*.xlsx~*",
                "*.xls~*",
                "*[Recovered]*",
                "*~$*.xlsx",
                "*~$*.xls"
            ]

            desktop_path = os.path.expanduser("~/Desktop")
            if os.path.exists(desktop_path):
                desktop_recovery_patterns = [
                    "*~$*.xlsx",
                    "*~$*.xls"
                ]

                for pattern in desktop_recovery_patterns:
                    files = glob.glob(os.path.join(desktop_path, pattern))
                    for file_path in files:
                        try:
                            if file_path in self.copied_files:
                                continue
                            os.remove(file_path)
                            logger.info(f"デスクトップの復旧ファイルを削除しました: {file_path}")
                        except Exception as e:
                            logger.debug(f"デスクトップ復旧ファイル削除エラー（無視可能）: {e}")

            for recovery_path in recovery_paths:
                if os.path.exists(recovery_path):
                    for pattern in recovery_patterns:
                        files = glob.glob(os.path.join(recovery_path, pattern))
                        for file_path in files:
                            try:
                                os.remove(file_path)
                                logger.info(f"復旧ファイルを削除しました: {file_path}")
                            except Exception as e:
                                logger.debug(f"復旧ファイル削除エラー（無視可能）: {e}")

        except Exception as e:
            logger.debug(f"復旧ファイル削除エラー（無視可能）: {e}")
