設計の解像度を上げるために、\*\*「JSONシナリオの読み込みから、画面操作、終了処理まで」\*\*の一連の流れを表す詳細シーケンス図を作成しました。

この図では、特に\*\*「変数の解決（Context）」**と**「操作の振り分け（Dispatcher/Action）」**、そして**「Page Objectの呼び出し」\*\*がどのように連携しているかに注目してください。

-----

# E2Eテスト自動化フレームワーク 詳細シーケンス図

## 1\. シーケンス図 (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    
    actor User as User (CLI)
    participant Pytest as Pytest Engine
    participant Loader as ScenarioLoader
    participant Runner as TestRunner
    participant Ctx as Context (Store)
    participant Dispatch as ActionDispatcher
    participant Action as ConcreteAction<br/>(UI/System/Verify)
    participant Page as PageObject / Registry
    participant App as Windows App (AUT)
    participant Report as Reporter / Hooks

    %% --- Phase 1: Initialization & Collection ---
    rect rgb(240, 248, 255)
        note right of User: Phase 1: Setup
        User->>Pytest: pytest実行 (with --env=stg)
        Pytest->>Report: pytest_sessionstart
        Report->>Ctx: Config読み込み & 初期化
        Pytest->>Loader: pytest_generate_tests (シナリオ収集)
        Loader->>Loader: JSONファイル探索 & 解析
        Loader-->>Pytest: シナリオリスト (List[Scenario])
    end

    %% --- Phase 2: Test Execution Loop ---
    rect rgb(255, 250, 240)
        note right of User: Phase 2: Execution
        loop 各シナリオ実行 (test_main)
            Pytest->>Runner: execute_scenario(scenario_data)
            
            loop 各ステップ実行 (Steps Loop)
                
                %% 2.1 変数解決
                Runner->>Ctx: resolve_params(step.values)
                activate Ctx
                Ctx-->>Runner: 解決済みパラメータ
                deactivate Ctx

                %% 2.2 条件判定
                Runner->>Runner: check_condition(step.condition)
                alt 条件不一致 (Skip)
                    Runner->>Runner: Continue Next Step
                else 条件一致 (Run)
                    
                    %% 2.3 アクション振り分け
                    Runner->>Dispatch: dispatch(step_type, params)
                    Dispatch->>Action: インスタンス生成 (UIAction等)
                    Dispatch->>Action: execute(context)
                    activate Action

                    %% 2.4 画面操作 (Page Object Pattern)
                    opt UI操作系 (Click/Input)
                        Action->>Page: get_page(page_name)
                        Page-->>Action: Page Instance
                        Action->>Page: page.find_element(locator)
                        Page->>App: pywinauto find logic
                        App-->>Page: Element Wrapper
                        Page-->>Action: Element Object
                        Action->>App: 操作実行 (Click / SendKeys)
                    end

                    %% 2.5 値のキャプチャ (Capture)
                    opt 値取得・保存
                        Action->>App: Get Text / Property
                        App-->>Action: Value
                        Action->>Ctx: set_variable(key, value)
                    end

                    %% 2.6 検証 (Assertion)
                    opt 検証操作
                        Action->>Action: assert value == expected
                    end

                    Action-->>Dispatch: 完了
                    deactivate Action
                    Dispatch-->>Runner: Step Success
                end
            end
            
            Runner-->>Pytest: Scenario Pass
        end
    end

    %% --- Phase 3: Error Handling & Teardown ---
    rect rgb(255, 240, 245)
        note right of User: Phase 3: Teardown
        alt 実行時エラー / アサーション失敗
            Pytest->>Report: pytest_runtest_makereport (Hook)
            Report->>App: スクリーンショット撮影
            Report->>Report: エラーログ保存
        end

        Pytest->>Report: pytest_sessionfinish
        Report->>Report: HTMLレポート生成
        Report->>User: Teams通知送信 / 終了
    end
```

## 2\. フローの詳細解説

図中の主要な処理ブロックについて解説します。

### Phase 1: セットアップと収集 (Setup Phase)

1.  **動的テスト生成:** `pytest` の標準機能である `pytest_generate_tests` フックを利用します。ここでJSONファイルを全て読み込み、「シナリオの数だけテスト関数（`test_main`）をパラメータ化して生成」します。これにより、テスト結果には `test_main[login_scenario]`, `test_main[order_scenario]` のように個別に表示されます。
2.  **Configの一元化:** `config.ini` の内容は最初に `Context` にロードされ、以降はシングルトン的に振る舞います。

### Phase 2: 実行ループ (Execution Phase)

このフレームワークの核心部分です。

  * **変数解決 (`resolve_params`):**
      * ステップを実行する**直前**に、パラメータ内の `${...}` を解決します。
      * これにより、前のステップで画面から取得（Capture）した値を、次のステップの入力値として使うことが可能になります。
  * **Page Objectの遅延ロード:**
      * すべてのPage Objectを最初に初期化するのではなく、アクションが必要としたタイミングで `PageRegistry` から呼び出します（Lazy Loading）。
      * `UIAction` クラスは「どの画面の」「どの要素を」操作するかだけをJSONから受け取り、実際の検索ロジックは Page Object に委譲します。

### Phase 3: エラーハンドリング (Teardown Phase)

  * **フックによる自動撮影:**
      * `try-except` を各ステップに書くのではなく、pytestの `pytest_runtest_makereport` フックを利用します。テストが `Failed` ステータスになった瞬間を検知し、自動的にデスクトップ全体のスクリーンショットを取得します。
