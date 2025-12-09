# 共有シナリオのログ抑制設計

## 背景
- `run_scenario` で展開される共有シナリオが多いと、各ステップの info ログが増え、run ログが読みにくくなる。
- 共有シナリオを呼び出す側で「今回はログを出さない」オプションを選びたいが、デフォルトは従来通りログを出す。

## 要件
- シナリオ JSON の `type: "run_scenario"` で、共有シナリオ内ステップの実行ログ出力有無を params で指定できる。
- 省略時はログ出力 ON（従来と同じ）。
- 無効化対象は Runner が出力するステップ開始/スキップの info ログ。エラー/例外ログは常に出力する。
- `args` の適用や変数解決、実行順序は従来通り。`run_scenario` のネストでも指定を引き継ぐ。
- 既存シナリオの挙動・構文を壊さない。

## 仕様（シナリオ記述）
- `run_scenario` の `params` に `log`（bool, デフォルト true）を追加。
- `log: false` を指定した場合、その呼び出しで展開された共有シナリオ配下のステップは info ログを出力しない。
- 例:
```json
{
  "name": "Run shared login silently",
  "type": "run_scenario",
  "params": {
    "path": "common/login.json",
    "args": {
      "login_user": "admin_user",
      "login_password": "secret_password"
    },
    "log": false
  }
}
```
- ネストした `run_scenario` も、親が `log: false` なら子もデフォルトで log: false として扱う（子で明示 true を指定すれば再度有効化）。

## 実装方針
### シナリオ展開（ScenarioLoader）
- `_expand_steps` に `parent_log_enabled: bool = True` を追加し、展開済みステップに `_log_enabled` メタデータを付与する。
- `run_scenario` 検知時:
  - `child_log_enabled = parent_log_enabled and params.get("log", True)` で有効/無効を決定。
  - `args` 用の自動挿入ステップ、および共有シナリオから読み込んだ各ステップに `_log_enabled = child_log_enabled` を付ける（既に付与済みなら AND で引き継ぎ）。
  - ネストした `run_scenario` を展開するときは `parent_log_enabled = child_log_enabled` で再帰させ、抑制設定を伝搬。
- `_source` 付与や変数解決ロジックは既存のまま。

### 実行時ログ制御（Runner）
- ステップ実行前に `log_enabled = step.get("_log_enabled", True)` を確認。
- `log_enabled` が false の場合は、`"Executing step..."` や条件未満による `"Skipping step..."` 等の info ログを出さない。
- 例外発生時の `logger.error` / `logger.debug(traceback...)` は常に出力し、問題調査の手掛かりを残す。
- 挙動差分は info ログ抑制のみのため、テストやスクリーンショット取得など周辺処理は影響なし。

## 互換性と影響範囲
- `log` を指定しない既存 `run_scenario` は `log = true` として扱われ、現行ログ出力が維持される。
- `steps` 直下の通常ステップにはメタデータを付けないため、影響は共有シナリオ展開部分に限定。
- `_log_enabled` は先頭にアンダースコアを付けた内部フィールドで、`params` とは分離されているためアクション実行には影響しない。

## テスト観点
- `log: false` 指定時に共有シナリオ配下のステップ開始ログが run ログに出ないことを確認（トップレベルステップは表示される）。
- 例外発生時にエラーログが出力されること（抑制されないこと）。
- ネストした共有シナリオで親 `log: false` が子に伝搬すること、`log: true` で再有効化できること。
- `log` 未指定のシナリオで従来と同じログが出る回帰確認。
