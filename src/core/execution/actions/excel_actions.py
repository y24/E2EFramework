#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel actions dispatched from scenario JSON.
"""

import logging
from typing import Any, Dict

from src.core.execution.actions.action_dispatcher import ActionDispatcher
from src.core.execution.actions.base_action import BaseAction
from src.pages.excel_page import ExcelPage

logger = logging.getLogger(__name__)


class ExcelAction(BaseAction):
    """Excel operations via ExcelPage."""

    def execute(self, params: Dict[str, Any]):
        action = params.get('action')

        if not action:
            raise ValueError("Excel action requires 'action' parameter")

        excel = ExcelPage()

        if action == 'start_excel':
            file_path = params.get('file_path')
            result = excel.start(file_path)
            if not result:
                raise Exception(f"Failed to start Excel with file: {file_path}")
            logger.info(f"Excel started with file: {file_path}")

        elif action == 'select_cell':
            cell_address = params.get('cell_address')
            row = params.get('row')
            column = params.get('column')

            if cell_address:
                result = excel.select_cell(cell_address=cell_address)
            elif row is not None and column is not None:
                result = excel.select_cell(row=row, column=column)
            else:
                raise ValueError("select_cell requires 'cell_address' or 'row' and 'column'")

            if not result:
                raise Exception(f"Failed to select cell: {cell_address or f'({row}, {column})'}")

        elif action == 'input_text':
            value = params.get('value', '')
            result = excel.input_text(str(value))
            if not result:
                raise Exception(f"Failed to input text: {value}")

        elif action == 'ribbon_shortcut':
            shortcut = params.get('shortcut')
            if not shortcut:
                raise ValueError("ribbon_shortcut requires 'shortcut' parameter")
            result = excel.execute_ribbon_shortcut(shortcut)
            if not result:
                raise Exception(f"Failed to execute ribbon shortcut: {shortcut}")

        elif action == 'save_file':
            file_path = params.get('file_path')
            result = excel.save(file_path)
            if not result:
                raise Exception("Failed to save file")

        elif action == 'close_workbook':
            save = params.get('save', False)
            result = excel.close_workbook(save=save)
            if not result:
                raise Exception("Failed to close workbook")

        elif action == 'exit_excel':
            excel.quit()
            ExcelPage.reset()
            logger.info("Excel terminated")

        elif action == 'handle_dialog':
            title_patterns = params.get('title_patterns', [])
            key_action = params.get('key_action', '{ESC}')
            timeout = params.get('timeout', 10)
            result = excel.handle_dialog(title_patterns, key_action, timeout)
            if not result:
                logger.warning(f"Dialog handling may have failed: {title_patterns}")

        else:
            raise ValueError(f"Unknown Excel action: {action}")


ActionDispatcher.register('excel', ExcelAction)
