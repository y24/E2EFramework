"""
保存ダイアログの構造を調査するスクリプト
"""
import time
from pywinauto import Desktop, Application

# メモ帳を起動
app = Application(backend='uia').start('notepad.exe')
time.sleep(1)

# Desktopからメモ帳ウィンドウを取得
desktop = Desktop(backend='uia')
notepad = desktop.window(title_re=".*(Notepad|メモ帳).*")
notepad.wait('exists', timeout=5)

# エディタにテキスト入力
editor = notepad.child_window(control_type="Document")
if not editor.exists(timeout=1):
    editor = notepad.child_window(control_type="Edit")
editor.type_keys("テスト", with_spaces=True)
time.sleep(0.5)

# Ctrl+Shift+Sで「名前を付けて保存」ダイアログを開く
editor.type_keys("^+s")
time.sleep(2)

# 保存ダイアログを取得
save_dialog = desktop.window(title_re=".*(Save [Aa]s|名前を付けて保存).*")
if save_dialog.exists(timeout=3):
    print("保存ダイアログが見つかりました")
    print(f"ダイアログのタイトル: {save_dialog.window_text()}")
    print(f"ダイアログのクラス名: {save_dialog.class_name()}")
    print("\n=== ダイアログの子要素一覧 ===")
    
    # すべての子要素を表示
    save_dialog.print_control_identifiers()
    
    print("\n=== ボタンコントロールの検索 ===")
    # ボタンを検索
    buttons = save_dialog.children(control_type="Button")
    for i, btn in enumerate(buttons):
        try:
            print(f"ボタン {i}: テキスト='{btn.window_text()}', AutomationId='{btn.automation_id()}'")
        except:
            print(f"ボタン {i}: 情報取得失敗")
    
    print("\n=== キャンセルボタンの検索テスト ===")
    # 様々な方法でキャンセルボタンを検索
    try:
        cancel1 = save_dialog.child_window(title="キャンセル", control_type="Button")
        print(f"方法1 (title='キャンセル'): exists={cancel1.exists()}")
    except Exception as e:
        print(f"方法1 失敗: {e}")
    
    try:
        cancel2 = save_dialog.child_window(title_re=".*キャンセル.*", control_type="Button")
        print(f"方法2 (title_re='.*キャンセル.*'): exists={cancel2.exists()}")
    except Exception as e:
        print(f"方法2 失敗: {e}")
    
    try:
        cancel3 = save_dialog.child_window(title_re=".*(Cancel|キャンセル).*", control_type="Button")
        print(f"方法3 (title_re='.*(Cancel|キャンセル).*'): exists={cancel3.exists()}")
    except Exception as e:
        print(f"方法3 失敗: {e}")
    
    try:
        cancel4 = save_dialog.child_window(auto_id="1", control_type="Button")
        print(f"方法4 (auto_id='1'): exists={cancel4.exists()}")
    except Exception as e:
        print(f"方法4 失敗: {e}")
    
    # ESCキーでダイアログを閉じる
    time.sleep(1)
    save_dialog.type_keys("{ESC}")
    time.sleep(0.5)
    
else:
    print("保存ダイアログが見つかりませんでした")

# メモ帳を閉じる
notepad.type_keys("%{F4}")
time.sleep(0.5)

print("\n調査完了")
