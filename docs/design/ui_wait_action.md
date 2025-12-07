# UI待機アクション (type: wait) 拡張仕様

## 目的
- UI要素の状態変化をシナリオから待機できるようにし、明示的な`type: wait`ステップとして扱う。
- 以下の待機ニーズを満たす: (1) 特定ウインドウの出現待ち、(2) 特定要素の非表示待ち、(3) 特定要素のクリック可能になるまで待機。
- 待機ごとに個別のタイムアウトを指定できるようにし、タイムアウト時は原因をログ/例外で示す。

## シナリオ記述仕様（新アクション）
- 新アクション種別 `type: "wait"` を追加。`operation: "wait"` を使う既存のwebアクションとは別物として扱い、UI/デスクトップ向け待機を担う。
- Page Object で解決できる `module.Class.property` 形式をターゲット指定の基本とする。ウインドウを待つ場合は `window` プロパティの指定を推奨。

### パラメータ
| param | 必須 | 型/デフォルト | 説明 |
| --- | --- | --- | --- |
| mode | Yes | string | 待機対象の種類。`window_appears` / `element_hidden` / `element_clickable` をサポート。 |
| target | 条件次第 | string | 待機対象。`mode` が `window_appears` の場合はウインドウ要素、他は任意の要素。`module.Class.property` 形式。 |
| timeout | No | float, 10.0 | 待機上限（秒）。ステップごとに指定可能。未指定時は既定値を使用。 |
| interval | No | float, 0.5 | ポーリング間隔（秒）。連打による負荷を避けるための最小スリープ。 |
| require_visible | No | bool, true | `window_appears` 用。true なら `exists` かつ `visible` になるまで待機。 |
| save_as | No | string | 待機結果（true/false）を `Context` に保存するキー。タイムアウト時は false 保存後に例外を送出。 |

### 振る舞い
- 共通: `time.monotonic()` で期限を算出し、`interval` ごとに状態を確認。期限超過で `TimeoutError` を送出（ログに mode/target/timeout を含める）。`save_as` 指定時は結果を必ず書き込む。
- `mode: window_appears`
  - `element.wait('exists')` を基本とし、`require_visible` が true なら `wait('visible')` も実施。
  - Page Object の `window` プロパティを前提にしつつ、要素解決エラーは即時失敗。
- `mode: element_hidden`
  - `exists()` が false になれば成功。
  - `exists()` が true でも `is_visible()`（利用可能な場合）が false であれば成功扱い。
  - いずれも満たされない場合は期限までポーリング。
- `mode: element_clickable`
  - まず存在チェック（`exists()`/`wait('exists')`）。次に `wait('visible')` と `wait('enabled')` を組み合わせてクリック可能を判定。
  - `is_enabled()` / `is_visible()` が取得できる場合は二重確認し、安定性を優先。

### シナリオ記述例
```json
{
  "name": "保存ダイアログの出現を待つ",
  "type": "wait",
  "params": {
    "mode": "window_appears",
    "target": "notepad_page.NotepadPage.save_dialog",
    "timeout": 8
  }
}
{
  "name": "保存ボタンが消えるまで待つ",
  "type": "wait",
  "params": {
    "mode": "element_hidden",
    "target": "notepad_page.NotepadPage.save_button",
    "timeout": 5,
    "interval": 0.3
  }
}
{
  "name": "送信ボタンが押下可能になるまで待つ",
  "type": "wait",
  "params": {
    "mode": "element_clickable",
    "target": "form_page.FormPage.submit_button",
    "timeout": 12,
    "save_as": "CAN_CLICK_SUBMIT"
  }
}
```

## 実装方針
- 新規 `WaitAction` を `src/core/execution/actions/wait_action.py` に追加し、`ActionDispatcher.register('wait', ...)` で登録。`__init__.py` にもインポートを追加する。
- ターゲット解決は `ConditionEvaluator._resolve_element` と同等のロジックを共通化するヘルパー（例: `src/utils/element_resolver.py`）を用意して再利用し、UIAction/VerifyAction/ConditionEvaluator との重複を解消する。
- 待機ロジックは `mode` ごとにメソッド分割し、`time.monotonic()` + `while` ループでポーリング。pywinauto の `wait`/`exists`/`is_visible`/`is_enabled` を組み合わせ、取得できない属性は例外を飲み込みつつログに残す。
- 例外メッセージには `mode`, `target`, `timeout`, 最後に観測した状態を含め、デバッグ性を確保する。`save_as` 指定時は成功/失敗に関わらず結果を書き込み、失敗時は例外を再送出してステップを失敗させる。
- 将来の拡張（`element_text_equals` や `process_exit` など）に備え、`mode` のディスパッチを辞書/関数マップで実装し、簡単に追加できる構造にする。
- ドキュメント更新: `docs/knowledge/action_reference.md` に `type: wait` のパラメータ表を追記し、サンプルシナリオにも新モードを1つ追加する。