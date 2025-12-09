# ステップ無視フラグ（ignore）設計

## 1. 背景・目的
- デバッグや一時的な回避対応で、特定ステップのみ実行をスキップしたいニーズがある。
- 既存のシナリオ JSON にはスキップ指示の手段がなく、コメントアウトやファイル分割が必要だった。
- `ignore: true` を指定したステップを安全に飛ばし、ログに明示的に残す挙動を追加する。

## 2. 要件
- シナリオ JSON の各ステップにオプションのブール `ignore` フィールドを追加する。省略時は `false` と同等。
- `ignore` が `true` のステップは実行せず、次のステップへ進む。
- スキップしたことを INFO ログに出力する（どのステップが無視されたか分かること）。
- 条件付き実行（`condition`）よりも `ignore` 判定が優先される。
- 共有シナリオ呼び出し（`run_scenario`）にも適用でき、全展開ステップが走らないことを保証する。
- 既存シナリオは挙動変化なし（後方互換）。

## 3. 仕様
### 3.1 シナリオ JSON 拡張
- 各ステップに `ignore` を追加可能。
- 例:
```json
{
  "name": "テキスト入力",
  "type": "ui",
  "ignore": true,
  "params": {
    "operation": "input",
    "target": "notepad_page.NotepadPage.editor",
    "value": "debug input"
  }
}
```

### 3.2 実行フロー
- Runner はステップループで最初に `ignore` を評価する。
  - `ignore` が真なら: `Executing step` ログの直後に `Skipping step '<name>' because ignore=true`（`_source` があればプレフィックス付き）を INFO で出力し、以降の処理（条件評価・パラメータ解決・アクション実行）を行わずに次へ進む。
  - `ignore` が偽/未指定なら: 既存フローを継続（条件→アクション）。
- 条件（`condition`）が指定されていても無視フラグが優先され、条件は評価しない。

### 3.3 `run_scenario` との扱い
- `run_scenario` ステップに `ignore: true` が付いた場合、共有シナリオの展開自体を行わず、親ステップとしてスキップログのみ出す。
- `run_scenario` 内の個別ステップに `ignore` を書いた場合は、通常の拡張後ステップにフラグが残るため、そのステップ単位でスキップされる。
- 自動挿入する変数設定ステップ（`Set arguments for ...`）も、呼び出し元ステップが `ignore: true` の場合は生成しない。

### 3.4 ログ出力フォーマット
- 既存の `[<source>] <step name>` 形式のプレフィックスを踏襲。
- スキップログ例（共有シナリオ由来のステップの場合）:
  - `Executing step: [common/login.json] ユーザーID入力`
  - `Skipping step 'ユーザーID入力' because ignore=true`
- `run_scenario` を丸ごと無視した場合:
  - `Executing step: [common/login.json] run_scenario(common/login.json)`
  - `Skipping step 'run_scenario(common/login.json)' because ignore=true`

## 4. 実装方針
- `Runner.execute_scenario`（`src/core/execution/runner.py`）
  - ステップ処理冒頭に `ignore` チェックを追加。
  - スキップ時は条件・変数解決・アクション呼び出しを行わない。
  - ログ文言は上記フォーマットに合わせ INFO で出力。
- `ScenarioLoader._expand_steps`（`src/core/scenario_loader.py`）
  - `run_scenario` で `ignore` が真なら共有シナリオをロードせず、元ステップをそのまま残す（`_source` 付与のみ）。
  - `ignore` が偽の場合は現行通り展開し、展開後ステップにも元の `_source` を引き継ぐ。
- 既存のアクション実装・条件評価・コンテキストは変更不要。

## 5. テスト観点
- `ignore` がないステップが従来通り実行されること。
- 単一ステップに `ignore: true` を指定した場合にスキップログが出て、アクションが呼ばれないこと。
- `condition` と併用した場合、`ignore` が優先されること。
- `run_scenario` に `ignore: true` を設定したとき、共有シナリオ内のステップや引数設定が実行されないこと。
- 共有シナリオ内の特定ステップだけに `ignore` を付けた場合、そのステップのみがスキップされること。
- ログ出力が `_source` プレフィックスを含むケースでも期待通りであること。

## 6. 移行と互換性
- `ignore` 未指定の既存シナリオは全て従来挙動のまま動作。
- 追加フィールドはオプションのため JSON スキーマ互換性を維持。
- 実装後もデフォルト値 `false` を明示的に扱うことで、不正な型（文字列 `"true"` など）が入っても真偽値変換の上で動作が安定するようにする。
