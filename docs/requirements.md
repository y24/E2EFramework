# E2Eテスト自動化フレームワーク 要件定義書

## 1\. 概要

本プロジェクトは、Windowsアプリケーションを中心としたE2Eテストを自動化するためのフレームワークを構築することを目的とする。
「保守性の高さ（Maintenance）」と「記述の柔軟性（Flexibility）」を最重要視し、Pythonエコシステムを活用したPage Object Model (POM) とデータ駆動（JSONシナリオ）を組み合わせたアーキテクチャを採用する。

## 2\. システム構成・アーキテクチャ

### 2.1 技術スタック

  * **言語:** Python 3.x
  * **UI操作:** `pywinauto` (Windows GUI), `subprocess` (CLI/Script)
  * **テストランナー:** `pytest` (実行制御、フック、レポート)
  * **補助ライブラリ:** `openpyxl`/`pandas` (帳票検証), `requests` (通知), `Pillow` (画像処理)

### 2.2 アーキテクチャ概念

  * **3層分離モデル:**
    1.  **データ層 (Scenarios/Config):** テスト手順と環境依存値を管理。
    2.  **ロジック層 (Core/Pages):** テストエンジンのコア機能と、画面操作の抽象化。
    3.  **実行層 (Runner/Utils):** pytestによる実行制御と、OS/外部連携の実装詳細。

## 2.3. システム概要

本フレームワークは、以下のコンポーネントから構成される。

1. **テスト実行エンジン**
   * pytest 上で動作するテストランナー層
   * CLIオプションを解析し、実行対象シナリオを決定
2. **シナリオ管理モジュール**
   * JSON形式のシナリオファイルを読み込み、テストケースやステップとして解釈
3. **UI操作層 (Page Object Model)**
   * 画面単位／機能単位の Page Object クラス群
   * pywinauto を利用して Windowsアプリケーションおよび外部アプリを操作
4. **検証 (アサーション) モジュール**
   * 画面要素/テキストの存在確認
   * 帳票ファイル（xlsx, txt 等）の内容検証
5. **スクリーンショットモジュール**
   * 任意タイミングおよび失敗時の自動スクリーンショット取得
6. **通知モジュール**
   * Teams webhook 等へのテスト結果通知
7. **設定管理モジュール**
   * INIファイルを読み込んで、環境依存情報をフレームワークに提供

## 3\. 機能要件

### 3.1 テスト実行・制御機能

  * **CLI実行:** シンプルなコマンド（`pytest`）で実行可能とする。
  * **フィルタリング:**
      * **タグ実行:** シナリオ内のタグ（`@smoke`等）による絞り込み。
      * **再帰的探索:** `scenarios` ディレクトリ配下の階層構造（サブフォルダ）を再帰的に探索し、テストケースを収集する。
  * **環境切り替え:** コマンドライン引数（例: `--env=stg`）により、読み込む設定ファイル（`config.ini`）を切り替える。

### 3.2 シナリオ定義・管理機能

  * **JSONシナリオ:** プログラミングレスなJSON形式で手順を記述する。
  * **Page Object連携:** 画面要素（Locator）はPage Objectクラスに分離し、JSONからは論理名で参照する。
  * **変数・設定値の統合管理 (Unified Context):**
      * **統一記法:** 設定値（Config）と動的変数（Runtime Variables）を区別なく `${KEY_NAME}` 形式で記述・参照可能とする。
      * **優先順位:** 同名のキーが存在する場合、実行中に生成された動的変数が設定値よりも優先される仕様とする。

### 3.3 動的パラメータと制御ロジック

  * **値のキャプチャ (Capture):**
      * 画面上のテキストやプロパティを取得し、変数として一時保存する。
      * 正規表現（Regex）による値の抽出・切り出しをサポートする。
  * **条件付き実行 (Conditional Execution):**
      * ステップごとに実行条件（`condition`）を付与可能とする。
      * 変数の値の一致や、UI要素（ポップアップ等）の有無を判定し、条件を満たさない場合はステップをスキップ（Skip）する（テスト失敗とはしない）。

### 3.4 操作・検証機能

  * **ハイブリッド操作:** 対象アプリに合わせて `uia` (UI Automation) と `win32` (Legacy) バックエンドを柔軟に切り替え可能とする。
  * **外部連携:** Excel/Webブラウザの操作、コマンド/スクリプト実行をサポートする。
  * **多角的な検証:**
      * **GUI:** 要素の存在、テキスト一致、有効/無効状態。
      * **帳票:** 出力されたファイル（Excel/Text）の内容検証。

### 3.5 レポーティング・通知機能

  * **スクリーンショット:**
      * **自動:** テスト失敗時（Assertion Error / Exception）にデスクトップ全体を自動撮影。
      * **任意:** シナリオ内の指定タイミングで撮影。
  * **Teams通知:** テスト完了後、実行結果（成功/失敗数）を指定のTeamsチャンネルへ通知する（通知条件は設定可能）。

## 4\. データ・設定ファイル仕様

### 4.1 環境設定ファイル (`config.ini`)

ユーザーが環境ごとに値を変更可能な設定ファイル。ユーザーは、以下のような情報を設定する。

  * **接続情報:** 接続先URL。
  * **認証情報:** ログインID、パスワード。
  * **パス設定:** 対象アプリの実行パス、帳票出力先フォルダ、エビデンス保存先。
  * **ログレベル:** ログ出力レベル。
  * **通知設定:** Webhook URL、通知条件。

### 4.2 テストシナリオファイル (`XXXX-XXX.json`)

テストシナリオは JSON 形式で定義し、少なくとも以下の情報を保持できること。

  * `id`: テストケースID
  * `name`: シナリオ名
  * `description`: シナリオの概要
  * `tags`: タグのリスト
  * `steps`: 手順の配列
    * 各ステップに以下の情報を含められること
      * 実行する操作 (Action)
      * 操作対象 (Target)
      * 入力値/パラメータ (Value)
      * 使用するpywinauto backend (`uia` または `win32`)
        * 指定しない場合は、`config.ini` で定義されたものを使用する
      * 期待結果（Expected）
      * 待機条件（特定ウインドウの出現、要素の存在、一定時間sleepなど）

### 4.3 Page Object 定義 (Python Class)

画面ごとの要素特定ロジック（ロケータ）を管理。

```python
class LoginPage:
    def __init__(self, app):
        self.window = app.window(title="Login")
    
    @property
    def username_field(self):
        return self.window.child_window(auto_id="txtUser", control_type="Edit")
    
    # ...他要素の定義
```

## 5\. 非機能要件

### 5.1 保守性 (Maintainability)

  * **分離の原則:** 「テストデータ（JSON/INI）」と「テストロジック（Python）」を完全に分離し、テストケースの追加・修正でコードを書き換える必要がない設計とする。
  * **DRY原則:** 共通の操作（設定ファイルのロード、初期化処理など）は `conftest.py` または共通メソッドとして実装し、重複を排除する。

### 5.2 実行環境 (Portability)

  * Windows 11 環境で動作すること。
  * Pythonの標準的な仮想環境（venv）で依存ライブラリを管理し、`pip install -r requirements.txt` で環境構築が完了すること。

## 6\. ディレクトリ構造案

単一責任の原則（SRP）に基づき、責務ごとにモジュールを分割する。

```text
project_root/
├── config/                    # 設定ファイル群
│   ├── config.ini             # 環境依存設定 (URL, UserID, Pathなど)
│   └── settings.json          # (Option) アプリ固有の定数定義など
├── scenarios/                 # テストシナリオ
│   ├── common/                # 共通・基盤系
│   │   ├── login.json
│   │   └── logout.json
│   ├── order/
│   │   ├── normal_order.json
│   │   └── cancel_order.json
│   └── master/
├── src/
│   ├── core/                  # フレームワーク中核 (Logic)
│   │   ├── context.py         # 変数・Config統合管理 (${}置換)
│   │   ├── scenario_loader.py # JSON読込・再帰探索・フィルタリング
│   │   └── execution/         # 実行エンジン (Execution Package)
│   │       ├── runner.py      # ステップ実行フロー制御
│   │       ├── condition.py   # スキップ判定ロジック
│   │       └── actions/       # 各種操作の実装 (Action Dispatcher)
│   │           ├── __init__.py    # アクションMap登録
│   │           ├── ui_actions.py  # GUI操作 (Click, Input)
│   │           ├── sys_actions.py # システム操作 (Start, Cmd)
│   │           └── verify_actions.py # 検証操作 (Assert)
│   ├── pages/                 # Page Object Model (画面定義)
│   │   ├── base_page.py       # 共通操作 (Click, Input等のラッパー)
│   │   ├── login_page.py      # ログイン画面の要素定義
│   │   └── ...
│   └── utils/                 # 実装詳細・ライブラリラッパー (How)
│       ├── screenshot.py      # スクリーンショット撮影・保存の実装
│       ├── driver_factory.py  # pywinauto接続管理
│       ├── file_validator.py  # ファイル読み込み検証
│       └── notifier.py        # HTTP通信・通知
├── tests/
│   ├── conftest.py            # Hook/Fixture (Setup, Teardown, 失敗検知)
│   └── test_runner.py         # pytest連携 (LoaderとRunnerのブリッジ)
├── reports/                   # (Git対象外) 実行結果出力先
│   ├── screenshots/           # エラー時・任意撮影の画像
│   └── logs/                  # 実行ログ
├── requirements.txt
└── pytest.ini
```

## 7\. コンポーネント詳細設計方針

### 7.1 `src/core/execution` の役割

実行ロジックの肥大化を防ぐため、以下のように役割を分担する。

  * **Runner:** 「条件チェック→アクション特定→変数解決→実行→保存」という一連の流れのみを管理する。
  * **Condition:** JSONの `condition` ブロックの解析と `True/False` の判定のみを行う。
  * **Actions:** 個別の操作（クリックする、検証するなど）の実装を持ち、`context` を受け取って作業を行う。

### 7.2 `tests/conftest.py` の役割

テストコード（ロジック）を含まず、ライフサイクル管理と「割り込み処理」に徹する。

  * **Setup:** コマンドライン引数の解析、初期化処理。
  * **Hook:** `pytest_runtest_makereport` を使用し、テスト失敗時に即座に `src.utils.capture` を呼び出す。
  * **Teardown:** アプリケーションのクリーンアップ、通知の送信。
