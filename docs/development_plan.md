# 実装計画 - E2E自動化フレームワーク

本計画書は、`docs/requirements.md` に記載された要件に基づき、E2E自動化フレームワークを構築するための手順をまとめたものです。

## ユーザー確認事項

> [!IMPORTANT]
> 本計画は新規構築（Greenfield）を想定しています。既存ファイルが存在する場合、上書きされる可能性があります。
> まずはフレームワークの基盤を実装し、その後、汎用的なアクションとサンプルテストを実装します。

## 変更提案

### 1. プロジェクト構成と初期設定

ディレクトリ構造の作成と、基盤となる設定ファイルを作成します。

#### [NEW] [requirements.txt](file:///d:/Script/E2EFramework/requirements.txt)
- 依存ライブラリの定義: `pytest`, `pywinauto`, `openpyxl`, `pandas`, `requests`, `Pillow`.

#### [NEW] [pytest.ini](file:///d:/Script/E2EFramework/pytest.ini)
- pytestの設定 (ログ設定、Pythonパスなど)。

#### [NEW] [config/config.ini](file:///d:/Script/E2EFramework/config/config.ini)
- 環境設定のプレースホルダー (URL, パス, 認証情報).

### 2. コアフレームワークロジック (`src/core`)

状態管理とシナリオ読み込みの仕組みを実装します。

#### [NEW] [src/core/context.py](file:///d:/Script/E2EFramework/src/core/context.py)
- `Context` クラス: 変数管理のためのシングルトン的なクラス (`${VAR}` の解決)。
- Configローダーの統合。

#### [NEW] [src/core/scenario_loader.py](file:///d:/Script/E2EFramework/src/core/scenario_loader.py)
- JSON ローダー: `scenarios/` ディレクトリ内の再帰的探索。
- `pytest_generate_tests` との統合ヘルパー。

### 3. テスト実行エンジン (`src/core/execution`)

ステップを解釈し、アクションを振り分けるエンジンを構築します。

#### [NEW] [src/core/execution/runner.py](file:///d:/Script/E2EFramework/src/core/execution/runner.py)
- `execute_scenario`: ステップ実行のメインループ。
- エラーハンドリングの統合。

#### [NEW] [src/core/execution/condition.py](file:///d:/Script/E2EFramework/src/core/execution/condition.py)
- ステップ内の `if` 条件ロジックの実装。

#### [NEW] [src/core/execution/actions/base_action.py](file:///d:/Script/E2EFramework/src/core/execution/actions/base_action.py)
- アクションの抽象基底クラス。

#### [NEW] [src/core/execution/actions/action_dispatcher.py](file:///d:/Script/E2EFramework/src/core/execution/actions/action_dispatcher.py)
- ステップタイプに基づき、特定のアクション (`ui`, `system`, `verify`) を生成するファクトリ。

### 4. アクションの実装 (`src/core/execution/actions`)

具体的なアクションロジックを実装します。

#### [NEW] [src/core/execution/actions/ui_actions.py](file:///d:/Script/E2EFramework/src/core/execution/actions/ui_actions.py)
- `UIAction`: PageObjects と連携して操作を実行 (Click, Input)。

#### [NEW] [src/core/execution/actions/sys_actions.py](file:///d:/Script/E2EFramework/src/core/execution/actions/sys_actions.py)
- `SystemAction`: OSレベルのコマンド実行、プロセス管理。

#### [NEW] [src/core/execution/actions/verify_actions.py](file:///d:/Script/E2EFramework/src/core/execution/actions/verify_actions.py)
- `VerifyAction`: 検証機能 (テキスト一致、ファイルの存在確認)。

### 5. Page Object Model (`src/pages`)

UI操作を抽象化します。

#### [NEW] [src/pages/base_page.py](file:///d:/Script/E2EFramework/src/pages/base_page.py)
- `BasePage`: `pywinauto` のラッパーメソッド (find, click_safe)。

#### [NEW] [src/utils/driver_factory.py](file:///d:/Script/E2EFramework/src/utils/driver_factory.py)
- `Application` インスタンスの管理 (起動, 接続, 終了)。

### 6. テストランナー統合 (`tests/`)

pytest とフレームワークを接続します。

#### [NEW] [tests/conftest.py](file:///d:/Script/E2EFramework/tests/conftest.py)
- `pytest_sessionstart`: Context/Config の初期化。
- `pytest_generate_tests`: ScenarioLoader の呼び出し。
- `pytest_runtest_makereport`: 失敗時のスクリーンショット撮影。

#### [NEW] [tests/test_runner.py](file:///d:/Script/E2EFramework/tests/test_runner.py)
- `test_main`: `Runner.execute_scenario` を呼び出すパラメータ化されたテスト関数。

## 検証計画

### 自動検証
実際の対象アプリがない場合でも検証できるよう、ダミーシナリオとダミーアプリ（メモ帳やモック）を使用します。

1.  **ユニットテスト**: 必要に応じてフレームワーク自体のユニットテストを行いますが、主には汎用ランナーを通じた検証を行います。
2.  **統合テスト**:
    - メモ帳を開き、テキストを入力し、内容を検証する `scenarios/test/sample.json` を作成します。
    - `pytest` を実行し、パスすることを確認します。
    - 意図的にステップを失敗させ、スクリーンショット取得とレポート機能を確認します。

### 手動検証
- `reports/logs` に生成されるログを確認します。
- 失敗時に `reports/screenshots` に保存されるスクリーンショットを確認します。
