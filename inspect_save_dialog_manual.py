"""
保存ダイアログの構造を調査するスクリプト（簡易版）
手動で保存ダイアログを開いてから実行してください
"""
import time
from pywinauto import Desktop

print("保存ダイアログを手動で開いてください...")
print("10秒待機します...")
time.sleep(10)

# Desktopから保存ダイアログを検索
desktop = Desktop(backend='uia')

print("\n=== すべてのウィンドウを検索 ===")
windows = desktop.windows()
for i, win in enumerate(windows):
    try:
        title = win.window_text()
        class_name = win.class_name()
        print(f"ウィンドウ {i}: タイトル='{title}', クラス='{class_name}'")
    except:
        pass

print("\n=== 保存ダイアログを検索 ===")
try:
    # 様々な方法で検索
    save_dialog = desktop.window(title_re=".*(Save|保存).*")
    if save_dialog.exists(timeout=1):
        print(f"保存ダイアログが見つかりました: {save_dialog.window_text()}")
        print(f"クラス名: {save_dialog.class_name()}")
        
        print("\n=== ダイアログの詳細情報 ===")
        save_dialog.print_control_identifiers()
        
        print("\n=== ボタンコントロールの検索 ===")
        buttons = save_dialog.descendants(control_type="Button")
        for i, btn in enumerate(buttons):
            try:
                text = btn.window_text()
                auto_id = btn.automation_id()
                class_name = btn.class_name()
                print(f"ボタン {i}: テキスト='{text}', AutomationId='{auto_id}', クラス='{class_name}'")
            except Exception as e:
                print(f"ボタン {i}: 情報取得失敗 - {e}")
        
    else:
        print("保存ダイアログが見つかりませんでした")
except Exception as e:
    print(f"エラー: {e}")

print("\n調査完了")
