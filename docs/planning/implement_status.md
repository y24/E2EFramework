# 実装状況確認レポート

本ドキュメントは、[要件定義書](requirements.md) に基づき、現在のコードベースの実装状況を整理したものです。

## 1. 実装済みの機能 (Implemented)

以下の機能は、基本設計通りに実装・配置されています。

### 1.1 アーキテクチャ・基盤
*   **ディレクトリ構造**: 提案された SRP (Single Responsibility Principle) に基づく構成 (`src/core`, `src/pages`, `src/execution` 等) が作成済み。
*   **Context管理**: `src/core/context.py` により、設定ファイル (`config.ini`) と実行時変数 (`variables`) の統合管理が実装済み。
*   **シナリオロード**: `src/core/scenario_loader.py` により、再帰的な JSON ファイルの探索とロードが実装済み。`pytest_generate_tests` を用いたパラメタライズも完了。

### 1.2 テスト実行エンジン
*   **Action Dispatcher**: `Actions` を動的に解決する仕組みが実装済み (`src/core/execution/actions/`).
    *   **UI Actions**: `click`, `input`, `read` 等の基本操作 (`pywinauto` 連携)。
    *   **Verify Actions**: `equals`, `contains`, `file_exists` の検証ロジック。
    *   **System Actions**: `sleep`, `command`, `start_app`。
*   **環境切り替え**: `pytest --env=NAME` による Config 切り替えサポート。

### 1.3 スクリーンショット
*   **自動取得**: `tests/conftest.py` のフックにより、テスト失敗時に自動でスクリーンショットを取得・保存する処理が実装済み。
*   **任意取得**: アクション (`screenshot_action` module implied via listings) として実装済み。


### 1.4 高度な条件分岐 (Advanced Conditions)
*   **要件**: UI要素の有無（ポップアップ等）を判定してステップをスキップする (要件 3.3)。
*   **実装状況**:
    *   `src/core/execution/condition.py` に `_evaluate_element_exists` メソッドを実装済み。
    *   `element_exists` 条件タイプをサポート。`target`、`expected`、`timeout` パラメータで動作を制御。
    *   サンプルシナリオ: `scenarios/test/element_exists_sample.json`

### 1.5 値のキャプチャ時の正規表現 (Regex Extraction)
*   **要件**: 画面から値を取得する際、正規表現で必要な部分のみを抽出・保存する (要件 3.3)。
*   **実装状況**:
    *   `src/core/execution/actions/ui_actions.py` に実装済み。`read` 操作時に `regex` パラメータを指定可能。
    *   検証シナリオ: `scenarios/test/regex_test.json`



### 1.6 帳票/ファイル内容検証 (File Validation)
*   **要件**: 出力されたファイル（Excel/Text）の内容を検証する (要件 3.4)。
*   **実装状況**:
    *   `src/utils/file_validator.py` を作成済み。Text (exact/contains/regex) と Excel (cell value) の検証をサポート。
    *   `src/core/execution/actions/verify_actions.py` に `file_content` 検証タイプを追加済み。
    *   検証シナリオ: `scenarios/test/file_validation_test.json`

---

## 2. 未実装・要対応の機能 (Not Implemented / TODO)

以下の要件は、ファイルが存在しないか、ロジックが不足しています。

### 1.7 通知機能 (Notification)
*   **要件**: テスト完了後、Teams 等へ結果を通知する。
*   **実装状況**:
    *   `src/utils/notifier.py` を作成し、Microsoft Teams への通知機能を実装。
    *   `tests/conftest.py` の `pytest_sessionfinish` に統合し、テスト完了時に自動実行。
    *   設定: `config.ini` の `[NOTIFICATION]` セクションで Webhook URL を管理 (URL未設定時はログ出力のみ)。

---

## 2. 未実装・要対応の機能 (Not Implemented / TODO)

以下の要件は、ファイルが存在しないか、ロジックが不足しています。

(ここに未実装項目があれば追記、現在はなし)



## 3. 今後のアクションプラン (推奨)

優先度順に以下の実装を推奨します。

1.  ~~**条件判定の拡張**: `ConditionEvaluator` に `element_exists` を追加。~~ ✅ 実装済み
2.  ~~**正規表現キャプチャの実装**: `UIAction` (read operation) の改修。~~ ✅ 実装済み
3.  **簡易通知機能**: `notifier.py` の作成と `conftest.py` への組み込み。
4.  **ファイル検証**: テキスト/CSV レベルなどの基本的なファイル内容検証アクションの追加。
