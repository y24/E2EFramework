# シナリオ Teardown セクション設計

## 1. 背景・目的
シナリオ中盤で例外やアサーションエラーが発生しても、環境の後片付けやリソース解放を確実に実行できるよう、`teardown` セクションをシナリオに追加する。従来は失敗時に直ちに終了するため、アプリ状態や外部リソースが汚れたまま残るリスクがあった。本設計では「メインの steps が途中で失敗しても、最後に teardown を必ず実行する」ことを保証する。

## 2. 要件
- シナリオ JSON に `teardown` 配列を追加できること（省略可・既存シナリオは非破壊）。
- `steps` の途中で例外が投げられても、シナリオ終了前に `teardown` が必ず実行されること。
- `teardown` は通常のステップと同じ解釈ルール（`type`・`params`・`condition`・変数解決・`run_scenario` 展開）で動くこと。
- `teardown` 内で失敗した場合も結果に反映し、ログ上で原因箇所を特定できること。
- 失敗時のスクリーンショット取得など既存の失敗ハンドリングと干渉しないこと。
- ステップ失敗時は、まずスクリーンショットを撮影し、その後に teardown を実行すること。

## 3. 仕様

### 3.1 シナリオフォーマット
`steps` と同階層に `teardown` を追加する。省略時は空配列として扱う。

```json
{
  "id": "ORDER-001",
  "name": "受注登録の正常系",
  "tags": ["smoke", "order"],
  "steps": [
    { "name": "アプリ起動", "type": "system", "params": { "action": "start_app" } },
    { "name": "ログイン", "type": "run_scenario", "params": { "path": "common/login.json" } },
    { "name": "受注登録", "type": "ui", "params": { "operation": "click", "target": "order_page.save" } }
  ],
  "teardown": [
    { "name": "ログアウト", "type": "ui", "params": { "operation": "click", "target": "global.logout_button" } },
    { "name": "アプリ終了", "type": "system", "params": { "action": "close_app" } }
  ]
}
```

### 3.2 実行フロー
- Runner はシナリオ読込時に `steps` と `teardown` を保持し、`execute_scenario` 内で以下の順序を取る。
  1. `steps` を先頭から順に実行（現行挙動通り、初回例外で残りの steps はスキップ）。
  2. 例外の有無にかかわらず、必ず `teardown` 全体を実行。
  3. いずれかで失敗があればシナリオを失敗として終了する。
- 条件付き実行（`condition`）や変数解決は通常ステップと同じ処理経路を通る。

### 3.3 失敗時の扱い
- `steps` 側の例外は記録して以後の `steps` を中断し、`teardown` 実行へ進む。
- `teardown` 実行中に発生した例外も記録する。
- 終了時の判定:
  - `steps` で失敗し、`teardown` が成功した場合: `steps` 側の例外を再送出。
  - `steps` が成功し、`teardown` で失敗した場合: `teardown` 側の例外を送出。
  - 両方失敗した場合: `steps` の例外を優先して送出し、ログに `teardown` 側の失敗も明示（例: `Teardown failed after main failure: ...` と連続出力、あるいは例外チェーンを使用）。

### 3.4 `run_scenario` との関係
- `teardown` 配列内にも `run_scenario` を書ける。ロード時に通常の `steps` と同じ拡張を行う。
- 共有シナリオ (`scenarios_shared`) に `teardown` を持たせる場合、現行のフラット展開方式では親シナリオの teardown とは独立に展開される（V1 では「共有シナリオ内 teardown の自動後処理保証」は対象外）。共有シナリオに共通後処理が必要な場合、呼び出し元の `teardown` に明示的に記述すること。

### 3.5 ログ・結果出力
- ログに `-- Teardown start --` のようなセクション開始を出力し、`_source` がある場合はステップ名に付加する。
- シナリオ結果は `steps` と `teardown` の両方が成功した場合のみ成功とみなす。
- 失敗時スクリーンショットのトリガー（pytest hook 等）は現行のエラー通知経路をそのまま使う。
- Runner 側でもステップ失敗を検知したら即座にスクリーンショットを試行し（失敗しても握りつぶす）、その後 teardown に進む。

## 4. 実装方針

### 4.1 Runner (`src/core/execution/runner.py`)
- `execute_scenario` を try/finally で二段構成にし、`steps` と `teardown` を個別関数で実行する。
- 疑似コード:
  ```python
  main_error = None
  try:
      self._execute_steps(steps)  # 現行ロジックを関数化
  except Exception as e:
      main_error = e
  finally:
      teardown_error = self._execute_teardown(teardown_steps)

  if main_error and teardown_error:
      self.logger.error("Teardown failed after main failure: %s", teardown_error)
      raise main_error
  if main_error:
      raise main_error
  if teardown_error:
      raise teardown_error
  ```
- `_execute_teardown` では `condition`/変数解決/`run_scenario` を含む通常のステップ実行を再利用し、ログで開始・終了を明示する。

### 4.2 ScenarioLoader (`src/core/scenario_loader.py`)
- シナリオ読み込み時に `teardown` があれば `self._expand_steps` を適用して展開する（省略時は空配列に正規化）。
- `_load_shared_steps` は `steps` だけを返す現行挙動を維持しつつ、`_source` 付与ロジックを `teardown` にも適用できるよう分岐をシンプル化する。

### 4.3 エラー報告・周辺
- 例外チェーンまたは連続ログで「メイン失敗」「teardown 失敗」を区別できるようにする。
- 既存のスクリーンショット/通知フックは Runner からの例外をそのまま伝播させることで動作する想定。追加対応が必要な場合は pytest フックで `teardown` エラーも通知対象に含める。

### 4.4 テスト方針
- ユニット: Runner に対し、(1) 正常系、(2) steps 失敗のみ、(3) teardown 失敗のみ、(4) 両方失敗、の 4 ケースで例外伝播順と実行回数を検証する。
- 統合: サンプルシナリオを用意し、`teardown` に `run_scenario`/`condition` を含むケースを実行して展開とログを確認する。

## 5. 移行・互換性
- 既存シナリオは `teardown` を省略したまま動作し、挙動変化はない。
- `teardown` を追加しても JSON スキーマの後方互換性は維持されるため、段階的に導入可能。
