import os
from datetime import datetime
from typing import Optional


def generate_normal_filename(test_id: str, test_name: str, additional_name: Optional[str] = None) -> str:
    """
    通常時のスクリーンショットファイル名を生成します。
    
    フォーマット: [{test_id}]{test_name}_{additional_name}_{datetime}.png
    
    Args:
        test_id (str): テストケースID
        test_name (str): テスト名
        additional_name (str, optional): 追加の名称
    
    Returns:
        str: 生成されたファイル名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ファイル名の構成要素をサニタイズ
    safe_test_id = sanitize_filename(test_id)
    safe_test_name = sanitize_filename(test_name)
    
    # ベースファイル名を構築
    if additional_name:
        safe_additional_name = sanitize_filename(additional_name)
        filename = f"[{safe_test_id}]{safe_test_name}_{safe_additional_name}_{timestamp}.png"
    else:
        filename = f"[{safe_test_id}]{safe_test_name}_{timestamp}.png"
    
    return filename


def generate_fail_filename(test_id: str, test_name: str) -> str:
    """
    テスト失敗時のスクリーンショットファイル名を生成します。
    
    フォーマット: FAIL_[{test_id}]_{test_name}_{datetime}.png
    
    Args:
        test_id (str): テストケースID
        test_name (str): テスト名
    
    Returns:
        str: 生成されたファイル名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ファイル名の構成要素をサニタイズ
    safe_test_id = sanitize_filename(test_id)
    safe_test_name = sanitize_filename(test_name)
    
    filename = f"FAIL_[{safe_test_id}]_{safe_test_name}_{timestamp}.png"
    
    return filename


def sanitize_filename(filename: str) -> str:
    """
    ファイル名に使用できない文字をアンダースコアに置換します。
    
    Args:
        filename (str): サニタイズ対象の文字列
    
    Returns:
        str: サニタイズされた文字列
    """
    # Windowsファイルシステムで使用できない文字
    invalid_chars = '<>:"/\\|?*'
    
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    return sanitized
