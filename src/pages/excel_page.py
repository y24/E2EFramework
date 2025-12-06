#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excelページオブジェクト
ExcelAutomationHelperをラップしてページパターンに統合

Note: ExcelはBasePageを継承しない。
ExcelAutomationHelperが独自にアプリケーション管理を行うため。
"""

from src.utils.excel_automation_helper import ExcelAutomationHelper


class ExcelPage:
    """Excelアプリケーションのページオブジェクト"""
    
    _helper = None  # シングルトンでヘルパーを管理
    
    def __init__(self):
        # BasePageを継承しない（Excelは独自のアプリ管理を行う）
        self._ensure_helper()
    
    @classmethod
    def _ensure_helper(cls):
        """ヘルパーのシングルトンを確保"""
        if cls._helper is None:
            cls._helper = ExcelAutomationHelper()
        return cls._helper
    
    @classmethod
    def get_helper(cls):
        """ヘルパーを取得"""
        return cls._ensure_helper()
    
    @property
    def helper(self):
        """ヘルパーインスタンスを取得"""
        return self._ensure_helper()
    
    @property
    def window(self):
        """Excelウィンドウを取得"""
        return self.helper.excel_window
    
    def start_with_file(self, file_path):
        """Excelを起動してファイルを開く"""
        return self.helper.start_excel(file_path)
    
    def select_cell(self, row=None, column=None, cell_address=None):
        """セルを選択"""
        return self.helper.select_cell(row=row, column=column, cell_address=cell_address)
    
    def input_text(self, text):
        """テキストを入力"""
        return self.helper.input_text(text)
    
    def click_ribbon_shortcut(self, shortcut):
        """リボン操作を実行"""
        return self.helper.click_ribbon_shortcut(shortcut)
    
    def save_file(self, file_path=None):
        """ファイルを保存"""
        return self.helper.save_file(file_path)
    
    def close_workbook(self, save=False):
        """ワークブックを閉じる"""
        return self.helper.close_workbook(save=save)
    
    def exit_excel(self):
        """Excelを終了"""
        return self.helper.exit_excel()
    
    def exists(self):
        """Excelウィンドウが存在するか"""
        return self.helper.excel_window is not None
    
    @classmethod
    def reset(cls):
        """ヘルパーをリセット（テスト間で状態をクリアする際に使用）"""
        if cls._helper:
            try:
                cls._helper.exit_excel()
            except:
                pass
            cls._helper = None
