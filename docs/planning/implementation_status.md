# コンディション・検証機能強化計画

E2Eフレームワークの条件分岐と検証機能を強化するための現状と実装計画。

**Status: Done**

## 1. コンディション (src/core/execution/condition.py)

### 実装状況
| 種類 | 説明 | 状況 | メモ |
| :--- | :--- | :--- | :--- |
| `variable` | 変数比較 | 既存 | equals, not_equals, contains をサポート |
| `element_exists` | 要素の存在確認 | 既存 | timeout をサポート |
| `element_text_empty` | 要素テキストが空 | Done | 「空なら入力」のロジックに使用 |
| `checkbox_state` | チェックボックスの ON/OFF | Done | 「OFF なら ON にする」のロジックに使用 |

### 実装詳細
- **element_text_empty**:
  - 対象: 要素パス
  - ロジック: テキスト取得 (get_value/window_text)。空文字または None なら True を返す。
- **checkbox_state**:
  - 対象: 要素パス (チェックボックス)
  - パラメータ: `expected` (bool - True は ON, False は OFF)
  - ロジック: トグル状態を確認 (`get_toggle_state()` または `is_checked()`)。

## 2. 検証 (src/core/execution/actions/verify_actions.py)

### 実装状況
| 種類 | 説明 | 状況 | メモ |
| :--- | :--- | :--- | :--- |
| `exists` | 要素が存在 | 既存 | |
| `not_exists` | 要素が存在しない | Done | 既存チェックの逆 |
| `contains` | テキストに含む (単純) | Done | 正規表現対応を強化 |
| `not_contains` | テキストに含まない | Done | contains の逆 |
| `clickable` | 要素がクリック可能 | Done | `is_enabled()` と `is_visible()` を確認？ |
| `matches` | 正規表現で全一致 | Done | 明示的な正規表現マッチ |

### 実装詳細
- **not_exists**:
  - `not element.exists()` を確認。
- **contains (強化)**:
  - `regex` パラメータを追加 (bool, デフォルト False)。
  - `regex=True` の場合は `re.search` を使用。
- **not_contains**:
  - contains の逆ロジック (正規表現対応を含む)。
- **clickable**:
  - `element.is_enabled()` を確認。(必要に応じて可視性も確認)

### 追加提案
- **file_size**: (検証に一部実装済み？厳密に要確認)。
- **list_count**: リスト/コンボの項目数を確認。

## 3. 実装計画 (完了)

1. **`src/core/execution/condition.py` を更新** (Done):
   - `_evaluate_text_empty` を追加。
   - `_evaluate_checkbox_state` を追加。
2. **`src/core/execution/actions/verify_actions.py` を更新** (Done):
   - `not_exists` を追加。
   - `contains` を正規表現対応に更新。
   - `not_contains` を追加。
   - `clickable` を追加。
3. **ドキュメント** (Done):
   - 完了したため `implementation_status.md` を更新済み。
