# pywinauto descendants()メソッドの活用

## 問題の背景

保存ダイアログのキャンセルボタンをクリックしようとした際、以下のエラーが発生しました:

```
Exception: UI Action Failed on notepad_page.NotepadPage.cancel_button: 
'NoneType' object has no attribute 'click_input'
```

## 原因: child_window()の検索範囲の制限

### 失敗したコード

```python
@property
def cancel_button(self):
    if self.save_dialog and self.save_dialog.exists():
        return self.save_dialog.child_window(title_re=".*(Cancel|キャンセル).*", control_type="Button")
    return None
```

### 問題点

`child_window()`は**直接の子要素のみ**を検索します。Windowsの標準ファイルダイアログは深い階層構造を持つため、ボタンが見つかりませんでした:

```
Window (Dialog) ← save_dialog
└── Pane
    └── Pane
        ├── ComboBox (ファイル名)
        ├── Button (保存)
        └── Button (キャンセル) ← ここにある！
```

`child_window()`は`Dialog`の直接の子（`Pane`）しか見ないため、その下にある`Button`を見つけられません。

## 解決策: descendants()メソッド

### 成功したコード

```python
@property
def cancel_button(self):
    dialog = self.save_dialog
    if dialog.exists(timeout=1):
        # Use descendants to search all child elements recursively
        buttons = dialog.descendants(control_type="Button")
        for btn in buttons:
            try:
                text = btn.window_text()
                if "キャンセル" in text or "Cancel" in text:
                    return btn
            except:
                continue
    return None
```

### descendants()の特性

| 特性 | 説明 |
|-----|------|
| **検索範囲** | 全ての子孫要素を**再帰的**に検索 |
| **戻り値** | マッチする要素のリスト |
| **パフォーマンス** | `child_window()`より遅いが、確実 |
| **用途** | 階層が深い、または不明な場合に有効 |

### なぜ有効だったか

1. **再帰的検索**: `Dialog > Pane > Pane > Button`のような深い階層でも全て探索
2. **柔軟性**: 要素の正確な位置を知らなくても検索可能
3. **確実性**: 階層構造が変わっても動作する可能性が高い

## pywinauto検索メソッドの比較

| メソッド | 検索範囲 | 速度 | 使用場面 |
|---------|---------|------|---------|
| `child_window()` | 直接の子要素のみ | 速い | 階層が浅く、位置が明確な場合 |
| `descendants()` | 全ての子孫要素（再帰的） | 遅い | 階層が深い、または不明な場合 |
| `window()` | トップレベルウィンドウ | 速い | ダイアログやメインウィンドウ |

## 実装のポイント

```python
# descendants()はリストを返すので、ループで処理
buttons = dialog.descendants(control_type="Button")
for btn in buttons:
    text = btn.window_text()
    if "キャンセル" in text:
        return btn
```

**重要**: 
- `descendants()`は複数の要素を返す可能性があるため、条件でフィルタリングが必要
- テキスト内容で判定することで、より確実に目的のボタンを特定

## 教訓

### いつdescendants()を使うべきか

✅ **使うべき場合**:
- Windowsの標準ダイアログ（ファイル選択、保存など）
- サードパーティ製アプリケーション（階層構造が不明）
- 動的に生成されるUI要素

❌ **避けるべき場合**:
- パフォーマンスが重要な場合
- 要素の位置が確実にわかっている場合
- 同じ条件の要素が複数存在する可能性がある場合（誤検出のリスク）

### ベストプラクティス

1. **まずchild_window()を試す** - 速度が速いため
2. **見つからない場合はdescendants()を使う** - 確実性を優先
3. **テキストやIDで絞り込む** - 複数マッチを避ける
4. **コメントに理由を記載** - なぜdescendants()を使ったか明記

## 検証結果

修正後のテスト実行:

```bash
pytest tests/test_runner.py::test_execute_scenario[SAMPLE-005] -v
```

**結果**: ✅ **1 passed in 6.92s**

- キャンセルボタンが正しく見つかる
- クリック操作が成功する
- ダイアログが閉じる

---

**作成日**: 2025-12-07  
**キーワード**: pywinauto, descendants, child_window, UI要素検索, 階層構造
