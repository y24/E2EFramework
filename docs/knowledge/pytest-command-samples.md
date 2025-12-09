
# pytest コマンドサンプル集

このプロジェクトは `pytest.ini` で `tests` ディレクトリを対象にし、`tests/test_runner.py` が JSON シナリオを実行するエントリーポイントです。主に使うオプションは `--env`（設定セクション）と `--tag`（シナリオの `tags` フィルタ）です。`ScenarioLoader` がシナリオ ID を pytest のパラメータ ID として付与するため、`-k "<ID>"` で個別実行できます。

## 代表的な実行例
- すべてのシナリオを既定環境で実行  
  ```bash
  pytest
  ```

- シナリオ系テストのみを冗長ログ付きで実行
  ```bash
  pytest -vv tests/test_runner.py
  ```

- 特定タグのシナリオだけを実行（`tags` に `sample` を含むもの）
  ```bash
  pytest tests/test_runner.py --tag sample
  ```

- 複数タグを OR で指定（`tag1` または `tag2` を含むシナリオを残す。カンマ区切り、空白はトリムされます）  
  ```bash
  pytest tests/test_runner.py --tag "tag1,tag2"
  ```

- 特定シナリオ ID（例: `SAMPLE-001`）だけを実行
  ```bash
  pytest tests/test_runner.py -k "SAMPLE-001"
  ```

- 複数シナリオ ID を論理和で実行
  ```bash
  pytest tests/test_runner.py -k "SAMPLE-001 or SAMPLE-002"
  ```

- ID プレフィックスでグループ実行（例: `SAMPLE-00` でまとめてマッチ）
  ```bash
  pytest tests/test_runner.py -k "SAMPLE-00"
  ```

## レポート・出力の位置
- HTML レポート: `reports/<RunID>/report.html`
- スクリーンショット: `reports/<RunID>/screenshots/`
- ログ: `reports/<RunID>/run_<RunID>.log`

## 補足
- 追加のフィルタ（例: マーカー）を使う場合は通常の pytest オプション `-m` や `-k` を併用できます。
- `--tag` はシナリオ JSON の `tags` 配列に完全一致する文字列でフィルタします。タグは複数付与しておき、運用上の切り口（アプリ別、エリア別、重要度など）で組み合わせるのが推奨です。
