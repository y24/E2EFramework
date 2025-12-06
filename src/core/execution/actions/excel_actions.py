#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excelアクション
シナリオJSONからExcel操作を実行するアクションクラス
"""

import logging
from typing import Dict, Any

from src.core.execution.actions.base_action import BaseAction
from src.core.execution.actions.action_dispatcher import ActionDispatcher
from src.pages.excel_page import ExcelPage

logger = logging.getLogger(__name__)


class ExcelAction(BaseAction):
    """Excel操作アクション"""
    
    def execute(self, params: Dict[str, Any]):
        """
        Excelアクションを実行
        
        Args:
            params: アクションパラメータ
                - action: アクション名
                - その他のパラメータはアクションによって異なる
        """
        action = params.get('action')
        
        if not action:
            raise ValueError("Excel action requires 'action' parameter")
        
        # ページオブジェクトを取得
        excel = ExcelPage()
        helper = excel.helper
        
        if action == 'start_excel':
            # Excelを起動してファイルを開く
            file_path = params.get('file_path')
            result = helper.start_excel(file_path)
            if not result:
                raise Exception(f"Failed to start Excel with file: {file_path}")
            logger.info(f"Excel started with file: {file_path}")
        
        elif action == 'select_cell':
            # セルを選択
            cell_address = params.get('cell_address')
            row = params.get('row')
            column = params.get('column')
            
            if cell_address:
                result = helper.select_cell(cell_address=cell_address)
            elif row is not None and column is not None:
                result = helper.select_cell(row=row, column=column)
            else:
                raise ValueError("select_cell requires 'cell_address' or 'row' and 'column'")
            
            if not result:
                raise Exception(f"Failed to select cell: {cell_address or f'({row}, {column})'}")
        
        elif action == 'input_text':
            # テキストを入力
            value = params.get('value', '')
            result = helper.input_text(str(value))
            if not result:
                raise Exception(f"Failed to input text: {value}")
        
        elif action == 'ribbon_shortcut':
            # リボン操作
            shortcut = params.get('shortcut')
            if not shortcut:
                raise ValueError("ribbon_shortcut requires 'shortcut' parameter")
            result = helper.click_ribbon_shortcut(shortcut)
            if not result:
                raise Exception(f"Failed to execute ribbon shortcut: {shortcut}")
        
        elif action == 'save_file':
            # ファイルを保存
            file_path = params.get('file_path')
            result = helper.save_file(file_path)
            if not result:
                raise Exception("Failed to save file")
        
        elif action == 'close_workbook':
            # ワークブックを閉じる
            save = params.get('save', False)
            result = helper.close_workbook(save=save)
            if not result:
                raise Exception("Failed to close workbook")
        
        elif action == 'exit_excel':
            # Excelを終了
            helper.exit_excel()
            ExcelPage.reset()
            logger.info("Excel terminated")
        
        elif action == 'handle_dialog':
            # ダイアログを処理
            title_patterns = params.get('title_patterns', [])
            key_action = params.get('key_action', '{ESC}')
            timeout = params.get('timeout', 10)
            result = helper.handle_dialog(title_patterns, key_action, timeout)
            if not result:
                logger.warning(f"Dialog handling may have failed: {title_patterns}")
        
        else:
            raise ValueError(f"Unknown Excel action: {action}")


# アクションを登録
ActionDispatcher.register('excel', ExcelAction)
