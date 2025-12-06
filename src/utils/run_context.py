"""
実行コンテキスト情報を生成するユーティリティモジュール。
日時、git情報、ホスト名からユニークなフォルダ名を生成する。
"""
import socket
import subprocess
from datetime import datetime
from typing import Optional


def get_git_commit_short() -> str:
    """
    現在のgit commit hashを取得する（7文字の短縮形）。
    gitが利用できない場合は空文字列を返す。
    
    Returns:
        str: 短縮コミットハッシュ、または空文字列
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short=7', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return ""


def get_git_branch() -> str:
    """
    現在のgitブランチ名を取得する。
    gitが利用できない場合は空文字列を返す。
    
    Returns:
        str: ブランチ名、または空文字列
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return ""


def get_hostname() -> str:
    """
    現在のマシンのホスト名を取得する。
    
    Returns:
        str: ホスト名
    """
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def sanitize_folder_name(name: str) -> str:
    """
    フォルダ名に使用できない文字を置換する。
    
    Args:
        name: 元の文字列
        
    Returns:
        str: サニタイズされた文字列
    """
    # Windowsフォルダ名で使用できない文字を置換
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name


def get_run_folder_name() -> str:
    """
    一意の実行フォルダ名を生成する。
    
    フォーマット:
    - git情報がある場合: YYYYMMDD-HHMMSS_<commit>_<branch>__<hostname>
    - git情報がない場合: YYYYMMDD-HHMMSS__<hostname>
    
    例:
    - 20250805-091210_ab12cd3_main__DESKTOP-ABC123
    - 20250805-091210__DESKTOP-ABC123
    
    Returns:
        str: ユニークなフォルダ名
    """
    # 日時部分
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # git情報を取得
    commit = get_git_commit_short()
    branch = get_git_branch()
    
    # ホスト名を取得
    hostname = get_hostname()
    
    # フォルダ名を構築
    parts = [timestamp]
    
    # git情報がある場合のみ追加
    if commit and branch:
        branch_sanitized = sanitize_folder_name(branch)
        parts.append(f"{commit}_{branch_sanitized}")
    
    # ホスト名を追加（二重アンダースコアで区切り）
    hostname_sanitized = sanitize_folder_name(hostname)
    folder_name = "_".join(parts) + f"__{hostname_sanitized}"
    
    return folder_name
