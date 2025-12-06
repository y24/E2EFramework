#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel UI自動化ヘルパークラス
pywinautoを使用してExcelのUI操作を自動化
"""

import time
import os
import winreg
import logging
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
from pywinauto.findwindows import find_window, find_windows

from src.utils.excel_automation_configs import ExcelConfig

logger = logging.getLogger(__name__)


def get_excel_path():
    """レジストリからExcelのインストールパスを取得"""
    try:
        # Office 2016以降（App Paths）
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe") as key:
            path, _ = winreg.QueryValueEx(key, "")
            if os.path.exists(path):
                logger.info(f"レジストリからExcelパスを取得: {path}")
                return path
    except Exception as e:
        logger.debug(f"App Pathsからの取得に失敗: {e}")

    try:
        # Office 2016/2019/365
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Office\16.0\Excel\InstallRoot") as key:
            path, _ = winreg.QueryValueEx(key, "Path")
            excel_path = os.path.join(path, "EXCEL.EXE")
            if os.path.exists(excel_path):
                logger.info(f"レジストリからExcelパスを取得: {excel_path}")
                return excel_path
    except Exception as e:
        logger.debug(f"Office 16.0からの取得に失敗: {e}")

    logger.warning("レジストリからExcelパスを取得できませんでした")
    return None


class ExcelAutomationHelper:
    """Excel UI自動化のヘルパークラス"""
    
    def __init__(self):
        self.app = None
        self.excel_window = None
        self.workbook = None
        self.copied_files = []  # コピーしたファイルのパスを記録

    def wait_for_excel_window(self, timeout=None, check_interval=None):
        """
        Excelウィンドウが表示されるまで動的に待機

        Args:
            timeout (float): 最大待機時間（秒）（Noneの場合は設定ファイルの値を使用）
            check_interval (float): チェック間隔（秒）（Noneの場合は設定ファイルの値を使用）

        Returns:
            bool: ウィンドウが見つかったかどうか
        """
        if timeout is None:
            timeout = ExcelConfig.get_timing('window_wait', 10)
        if check_interval is None:
            check_interval = 0.5

        logger.info(f"Excelウィンドウの表示を待機中... (タイムアウト: {timeout}秒)")

        process_name = ExcelConfig.get_excel_setting('process_name')
        elapsed_time = 0

        while elapsed_time < timeout:
            try:
                window_handle = find_window(process=process_name)
                if window_handle:
                    self.excel_window = self.app.window(handle=window_handle)
                    # ウィンドウが実際に表示されているかチェック
                    if self.excel_window.is_visible():
                        logger.info(f"Excelウィンドウを検出しました（{elapsed_time:.1f}秒後）")
                        return True
            except Exception as e:
                logger.debug(f"ウィンドウ検索中（{elapsed_time:.1f}秒）: {e}")

            time.sleep(check_interval)
            elapsed_time += check_interval

        return False

    def wait_for_dialog(self, title_patterns, timeout=None, check_interval=None):
        """
        指定されたタイトルパターンに一致するダイアログが表示されるまで待機

        Args:
            title_patterns (str or list): ダイアログタイトルのパターン（文字列またはリスト）
            timeout (float): 最大待機時間（秒）
            check_interval (float): チェック間隔（秒）

        Returns:
            tuple: (ダイアログが見つかったかどうか, ダイアログウィンドウオブジェクト)
        """
        try:
            if isinstance(title_patterns, str):
                title_patterns = [title_patterns]

            if timeout is None:
                timeout = ExcelConfig.get_timing('dialog_timeout', 10)
            if check_interval is None:
                check_interval = ExcelConfig.get_timing('dialog_check_interval', 0.5)

            logger.info(f"ダイアログの表示を待機中... (タイムアウト: {timeout}秒, パターン: {title_patterns})")

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    for pattern in title_patterns:
                        try:
                            dialog_window = find_window(title_re=f".*{pattern}.*")
                            if dialog_window:
                                logger.info(f"ダイアログを検出しました: {pattern}")
                                return True, dialog_window
                        except Exception as e:
                            logger.debug(f"ダイアログ検索エラー（パターン: {pattern}）: {e}")
                            continue

                    time.sleep(check_interval)

                except Exception as e:
                    logger.debug(f"ダイアログ待機中のエラー: {e}")
                    time.sleep(check_interval)

            logger.warning(f"ダイアログの表示待機がタイムアウトしました (パターン: {title_patterns})")
            return False, None

        except Exception as e:
            logger.error(f"ダイアログ待機エラー: {e}")
            return False, None

    def handle_dialog(self, title_patterns, key_action='{ESC}', timeout=10):
        """
        ダイアログを処理する（表示を待機してから適切なアクションを実行）

        Args:
            title_patterns (str or list): ダイアログタイトルのパターン
            key_action (str): 実行するキー操作
            timeout (float): ダイアログ表示待機時間（秒）

        Returns:
            bool: 処理が成功したかどうか
        """
        try:
            dialog_found, dialog_window = self.wait_for_dialog(title_patterns, timeout)

            if not dialog_found:
                logger.info(f"ダイアログは表示されませんでした (パターン: {title_patterns})")
                return True

            logger.info(f"ダイアログでアクション '{key_action}' を実行")

            try:
                if dialog_window:
                    dialog_window.set_focus()
                    time.sleep(ExcelConfig.get_timing('dialog_wait', 0.2))
            except Exception as e:
                logger.debug(f"ダイアログアクティベートエラー: {e}")

            time.sleep(ExcelConfig.get_timing('dialog_wait'))
            send_keys(key_action)
            time.sleep(ExcelConfig.get_timing('dialog_wait', 0.2))
            
            logger.info("ダイアログの処理が完了しました")
            return True

        except Exception as e:
            logger.error(f"ダイアログ処理エラー: {e}")
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

    def start_excel(self, file_path=None):
        """Excelを起動し、指定されたファイルを開く"""
        try:
            # 起動前に復旧ファイルを削除
            self._cleanup_recovery_files()

            # レジストリからExcelのパスを取得
            excel_path = get_excel_path()

            # Excelの一般的なインストールパスを試す
            excel_paths = [
                excel_path,
                r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
                r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
                r"C:\Program Files\Microsoft Office\Office16\EXCEL.EXE",
                r"C:\Program Files (x86)\Microsoft Office\Office16\EXCEL.EXE",
            ]

            # 有効なパスを見つける
            valid_excel_path = None
            for path in excel_paths:
                if path is None:
                    continue
                try:
                    if os.path.exists(path):
                        valid_excel_path = path
                        break
                except:
                    continue

            if valid_excel_path is None:
                logger.error("Excelが見つかりません。Excelがインストールされているか確認してください。")
                return False

            # Excelを起動
            if file_path and os.path.exists(file_path):
                cmd = f'"{valid_excel_path}" "{file_path}" /e'
                self.app = Application(backend='uia').start(cmd)
                logger.info(f"Excelファイルを開きました: {file_path}")
            else:
                self.app = Application(backend='uia').start(valid_excel_path)
                logger.info("新しいExcelを起動しました")

            # Excelウィンドウが表示されるまで動的に待機
            if not self.wait_for_excel_window():
                logger.warning("プロセス名でのウィンドウ検索に失敗、タイトルパターンを使用")
                try:
                    self.excel_window = self.app.window(title_re=ExcelConfig.get_excel_setting('window_title_pattern'))
                    self.excel_window.wait('visible', timeout=5)
                    logger.info("タイトルパターンでExcelウィンドウを検出しました")
                except Exception as e:
                    logger.error(f"タイトルパターンでのウィンドウ検索にも失敗: {e}")
                    raise Exception("Excelウィンドウを検出できませんでした")

            logger.info("Excelウィンドウの準備が完了しました")
            return True

        except Exception as e:
            logger.error(f"Excel起動エラー: {e}")
            import traceback
            traceback.print_exc()
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
            
            # 名前ボックスへ直接入力でセル移動（Ctrl+G よりも確実）
            send_keys(ExcelConfig.get_shortcut('go_to'))  # Ctrl+G でジャンプ
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
                    # 「保存」を選択
                    send_keys('{ENTER}')
                else:
                    # 「保存しない」を選択 (N キー)
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
            if self.app and self.app.is_process_running():
                self.app.kill()
                logger.info("Excelを終了しました")
        except:
            try:
                self.app.kill()
                logger.info("Excelを終了しました")
            except:
                pass

        self._cleanup_recovery_files()

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
