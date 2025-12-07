# デバッグアクション (debug action) の使い方

## 概要

デバッグアクションは、E2Eテストシナリオの開発時にUI要素の構造を調査するためのツールです。ページオブジェクトを作成する際に、対象アプリケーションのUI階層構造を把握するのに役立ちます。

## 背景

UI自動化において、以下のような問題が頻繁に発生します：

- 要素が見つからない（`'NoneType' object has no attribute 'click_input'`）
- ダイアログがデスクトップレベルなのか、親ウィンドウの子要素なのかわからない
- 正しい `control_type` や `class_name` がわからない

これらの問題を解決するために、シナリオファイルから呼び出せるデバッグ機能を実装しました。

## 使用可能なアクション

### 1. `list_desktop_windows` - デスクトップウィンドウのリスト

デスクトップ上のすべてのトップレベルウィンドウを一覧表示します。

```json
{
    "name": "デスクトップの全ウィンドウをリスト",
    "type": "debug",
    "params": {
        "action": "list_desktop_windows"
    }
}
```

#### パラメータ

| パラメータ | 型 | 説明 | 必須 |
|-----------|-----|------|------|
| `filter` | string | タイトルでフィルタ（部分一致） | No |
| `control_type` | string | コントロールタイプでフィルタ | No |

#### 使用例：メモ帳のウィンドウのみ表示

```json
{
    "name": "メモ帳のウィンドウのみ表示",
    "type": "debug",
    "params": {
        "action": "list_desktop_windows",
        "filter": "メモ帳"
    }
}
```

#### 出力例

```
=== Desktop Windows ===
  [タスク バー] control_type=Pane, class=Shell_TrayWnd
  [*Testcontent - メモ帳] control_type=Window, class=Notepad
  [Program Manager] control_type=Pane, class=Progman
=== End Desktop Windows ===
```

---

### 2. `list_descendants` - ページオブジェクトの子孫要素リスト

指定したページオブジェクトのすべての子孫要素を一覧表示します。ボタンやテキストフィールドなど、操作対象の要素を特定するのに最も有用です。

```json
{
    "name": "メモ帳の子孫要素をすべてリスト",
    "type": "debug",
    "params": {
        "action": "list_descendants",
        "target": "notepad_page.NotepadPage"
    }
}
```

#### パラメータ

| パラメータ | 型 | 説明 | 必須 |
|-----------|-----|------|------|
| `target` | string | ページオブジェクトパス | Yes |
| `filter` | string | テキストでフィルタ（部分一致） | No |
| `control_type` | string | コントロールタイプでフィルタ | No |
| `depth` | int | 表示する最大要素数 | No |

#### target の指定方法

- `notepad_page.NotepadPage` - NotepadPageクラスの`window`プロパティを使用
- `notepad_page.NotepadPage.window` - 明示的に`window`プロパティを指定
- `notepad_page.NotepadPage.save_dialog` - 特定のプロパティを指定

#### 使用例：ボタン要素のみ表示

```json
{
    "name": "メモ帳のボタンのみリスト",
    "type": "debug",
    "params": {
        "action": "list_descendants",
        "target": "notepad_page.NotepadPage",
        "control_type": "Button"
    }
}
```

#### 出力例

```
=== Descendants of notepad_page.NotepadPage ===
  [名前を付けて保存] control_type=Window, class=
  [保存フィールド] control_type=Tree, class=
  [保存(S)] control_type=Button, class=
  [キャンセル] control_type=Button, class=
Total: 45 elements (filtered to 4)
=== End Descendants ===
```

---

### 3. `check_dialog` - ダイアログ存在確認

特定のクラス名やタイトルを持つダイアログが存在するかを確認します。

```json
{
    "name": "Win32ダイアログの存在確認",
    "type": "debug",
    "params": {
        "action": "check_dialog",
        "class_name": "#32770"
    }
}
```

#### パラメータ

| パラメータ | 型 | 説明 | 必須 |
|-----------|-----|------|------|
| `class_name` | string | ダイアログのクラス名（例: `#32770`） | どちらか必須 |
| `title` | string | ダイアログのタイトル（部分一致） | どちらか必須 |
| `timeout` | float | 待機時間（秒）。デフォルト: 1 | No |

#### 出力例

```
=== Dialog Check ===
  [OK] Dialog FOUND: [名前を付けて保存] class=#32770, control_type=Dialog
=== End Dialog Check ===
```

または

```
=== Dialog Check ===
  [NG] Dialog NOT FOUND: class_name=#32770
=== End Dialog Check ===
```

---

## 実践的な使用シナリオ

### シナリオ1: 新しいページオブジェクトを作成する

1. アプリケーションを起動
2. `list_desktop_windows` でウィンドウのタイトルと `control_type` を確認
3. `list_descendants` でウィンドウ内の要素を確認
4. 必要な要素の `control_type` と `window_text` をメモ
5. ページオブジェクトのプロパティを実装

### シナリオ2: 要素が見つからないエラーをデバッグ

```
Exception: UI Action Failed on notepad_page.NotepadPage.cancel_button: 
'NoneType' object has no attribute 'click_input'
```

1. エラーが発生する前に `list_descendants` ステップを追加
2. 出力から目的の要素がリストに含まれているか確認
3. 含まれていない場合：
   - 別のウィンドウに存在する可能性 → `list_desktop_windows` で確認
   - 親ウィンドウが間違っている → 正しい親を探す
4. 含まれている場合：
   - `control_type` や `window_text` のマッチング条件を確認

### シナリオ3: ダイアログの構造を調べる

```json
[
    {"name": "保存ダイアログを開く", "type": "ui", "params": {...}},
    {"name": "待機", "type": "system", "params": {"action": "sleep", "duration": 2}},
    {"name": "デスクトップ確認", "type": "debug", "params": {"action": "list_desktop_windows"}},
    {"name": "親ウィンドウ確認", "type": "debug", "params": {"action": "list_descendants", "target": "notepad_page.NotepadPage"}}
]
```

---

## サンプルシナリオ

完全な使用例は `scenarios/sample/SAMPLE-009_debug_action_sample.json` を参照してください。

```bash
pytest --tag=debug
```

---

## 注意事項

- デバッグアクションは開発時のみ使用し、本番テストからは削除してください
- 大量の要素を持つウィンドウでは `depth` パラメータで出力を制限できます
- 出力はログファイルとコンソールの両方に表示されます

---

**作成日**: 2025-12-07  
**関連ファイル**: 
- `src/core/execution/actions/debug_action.py`
- `scenarios/sample/DEBUG-001_debug_action_sample.json`  
**キーワード**: debug, descendants, list_desktop_windows, check_dialog, UI調査, 要素特定
