# E2Eテスト自動化フレームワーク クラス設計

## 1. クラス図 (Class Diagram)

本プロジェクトのアーキテクチャ（Page Object Model + データ駆動）を表現したクラス図です。
保守性を高めるため、「コンテキスト（変数管理）」、「アクション（操作ロジック）」、「ページ定義（要素特定）」を疎結合に保つ設計としています。

```mermaid
classDiagram
    %% --- Pytest / Entry Point ---
    class TestEntrypoint {
        +test_main(scenario_id)
        +pytest_generate_tests()
    }
    note for TestEntrypoint "tests/test_runner.py\nPytest Parameterization\nGenerate tests per scenario"

    class PytestHooks {
        +pytest_runtest_makereport()
        +pytest_sessionstart()
        +pytest_sessionfinish()
    }
    note for PytestHooks "tests/conftest.py\nSetup/Teardown/Hook Mgmt"

    %% --- Core: Data & Context ---
    class ConfigLoader {
        +load_ini(env) dict
    }

    class Context {
        -variables: dict
        -config: dict
        +get(key)
        +set(key, value)
        +resolve_string(text) str
    }
    note for Context "Manage dynamic vars\nResolve ${VAR} syntax"

    class ScenarioLoader {
        +load_all(path) List~Scenario~
        +filter_by_tag(tag)
    }

    class Scenario {
        +id: str
        +steps: List~Step~
    }

    class Step {
        +action_type: str
        +target: str
        +value: Any
        +condition: str
    }

    %% --- Core: Execution Engine ---
    class TestRunner {
        +execute_scenario(scenario)
    }

    class ConditionEvaluator {
        +should_run(step, context) bool
    }

    class ActionDispatcher {
        +dispatch(step, context)
    }
    note for ActionDispatcher "Factory Pattern:\nString -> Action Class"

    %% --- Actions Strategy ---
    class BaseAction {
        <<Abstract>>
        +execute(step, context)
    }

    class UIAction {
        +execute()
        -perform_interaction()
    }

    class SystemAction {
        +execute()
        -run_process()
    }

    class VerifyAction {
        +execute()
        -assert_value()
    }

    %% --- Page Object Model ---
    class PageRegistry {
        +get_page(page_name) BasePage
    }

    class BasePage {
        +find_element(locator)
        +wait_for_element(locator)
    }

    class LoginPage {
        +username_field
        +password_field
        +login_btn
    }

    class OrderPage {
        +product_list
        +submit_btn
    }

    %% --- Utils / Infrastructure ---
    class DriverFactory {
        +get_app(backend)
        +connect()
        +kill()
    }

    class ScreenshotManager {
        +capture_screen(filename)
        +capture_element(element)
    }

    class Notifier {
        +send_teams_message(result)
    }

    %% --- Relationships ---
    TestEntrypoint ..> ScenarioLoader : Uses
    TestEntrypoint ..> TestRunner : Uses
    PytestHooks ..> Notifier : Uses (Teardown)
    PytestHooks ..> ScreenshotManager : Uses (On Failure)

    TestRunner --> Context : Holds state
    TestRunner --> ConditionEvaluator : Uses
    TestRunner --> ActionDispatcher : Uses

    ActionDispatcher ..> BaseAction : Creates/Calls

    BaseAction <|-- UIAction
    BaseAction <|-- SystemAction
    BaseAction <|-- VerifyAction

    UIAction ..> PageRegistry : Resolves Page
    PageRegistry ..> BasePage : Manages
    BasePage <|-- LoginPage
    BasePage <|-- OrderPage

    BasePage ..> DriverFactory : Uses pywinauto
    Context ..> ConfigLoader : Loads init