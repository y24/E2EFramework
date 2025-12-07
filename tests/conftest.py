import sys
import os

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import shutil
import logging
import base64
from datetime import datetime

try:
    import pytest_html.extras
except ImportError:
    pytest_html = None

# モジュールレベル変数：セッション全体で共有する実行フォルダ名
_run_folder_name = None

from src.core.context import Context
from src.core.scenario_loader import ScenarioLoader
from src.utils.driver_factory import DriverFactory
from src.utils.web_driver_factory import WebDriverFactory
from src.core.execution.runner import Runner
from src.utils.screenshot import ScreenshotManager
from src.utils.run_context import get_run_folder_name

def _get_run_folder():
    """実行フォルダ名を取得（セッション全体で同一の名前を返す）"""
    global _run_folder_name
    if _run_folder_name is None:
        _run_folder_name = get_run_folder_name()
    return _run_folder_name

def pytest_configure(config):
    """pytest起動時にHTMLレポートの出力パスを設定"""
    run_folder = _get_run_folder()
    base_reports = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports', run_folder))
    os.makedirs(base_reports, exist_ok=True)
    
    # HTMLレポートのパスを設定
    html_report_path = os.path.join(base_reports, 'report.html')
    config.option.htmlpath = html_report_path
    config.option.self_contained_html = True

def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="DEFAULT", help="Environment to run tests against")
    parser.addoption("--tag", action="store", default="", help="Filter scenarios by tag")

@pytest.fixture(scope="session", autouse=True)
def setup_session(request):
    """Global setup for the test session."""
    env = request.config.getoption("--env")
    
    # Initialize Context
    context = Context()
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/config.ini'))
    context.load_config(config_path, env)
    
    # 実行ごとの固有フォルダを生成（pytest_configureで設定済みのものを再利用）
    run_folder = _get_run_folder()
    base_reports = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports', run_folder))
    
    # ログとスクリーンショットのディレクトリを設定
    screenshot_dir = os.path.join(base_reports, 'screenshots')
    
    # Contextに保存（config.iniの値を上書き）
    context.set_variable('SCREENSHOTDIR', screenshot_dir)
    
    # ディレクトリを作成
    os.makedirs(base_reports, exist_ok=True)
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # ログファイルの設定
    log_file = os.path.join(base_reports, f'run_{run_folder}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    
    # ルートロガーにファイルハンドラを追加
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    # ファイルハンドラを後でクリーンアップするために保存
    request.config._log_file_handler = file_handler

    yield
    
    # Teardown
    # ファイルハンドラを削除してファイルを閉じる
    if hasattr(request.config, '_log_file_handler'):
        root_logger = logging.getLogger()
        root_logger.removeHandler(request.config._log_file_handler)
        request.config._log_file_handler.close()
    
    # Webブラウザを終了
    if WebDriverFactory.is_active():
        WebDriverFactory.close_browser()
    
    DriverFactory.close_app()

@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    """Log execution details after collection."""
    logging.info("Test Execution Summary")
    logging.info("-" * 40)
    
    # Log Filter Conditions
    tag = config.getoption("--tag")
    keyword = config.getoption("-k")
    mark = config.getoption("-m")
    
    conditions = []
    if tag:
        conditions.append(f"Tag: {tag}")
    if keyword:
        conditions.append(f"Keyword: {keyword}")
    if mark:
        conditions.append(f"Mark: {mark}")
        
    if conditions:
        logging.info(f"Filters: {', '.join(conditions)}")
    else:
        logging.info("Filters: None (All tests)")
        
    # Log Test Count
    logging.info(f"Total Tests to Run: {len(items)}")
    
    # Optional: Log list of tests if needed (can be verbose)
    # for item in items:
    #     logging.info(f"  - {item.nodeid}")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture screenshot on failure and attach to HTML report."""
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        screenshot_path = None
        try:
            from src.utils.screenshot_filename import generate_fail_filename
            from src.core.context import Context
            
            context = Context()
            output_dir = context.get_variable('SCREENSHOTDIR', 'reports/screenshots')
            
            # Get test info from context
            test_id = context.get_current_test_id()
            test_name = context.get_current_test_name()
            
            # Generate filename using new format
            filename = generate_fail_filename(test_id, test_name)
            
            # Use ScreenshotManager to take the screenshot
            manager = ScreenshotManager(output_dir=output_dir)
            screenshot_path = manager.capture_screen(filename=filename)
            
            if screenshot_path:
                logging.info(f"Screenshot saved to {screenshot_path}")
            else:
                logging.warning("Failed to take screenshot.")
        except Exception as e:
            logging.error(f"Failed to take screenshot: {e}")
        
        # HTMLレポートにスクリーンショットを添付
        if pytest_html is not None and screenshot_path and os.path.exists(screenshot_path):
            try:
                extras = getattr(rep, "extras", [])
                # base64エンコードで画像を埋め込み（self-contained対応）
                with open(screenshot_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                extras.append(pytest_html.extras.png(image_data))
                rep.extras = extras
            except Exception as e:
                logging.error(f"Failed to attach screenshot to report: {e}")

def pytest_generate_tests(metafunc):
    """Parametrize test functions based on JSON scenarios."""
    if "scenario" in metafunc.fixturenames:
        # Load scenarios
        scenarios_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scenarios'))
        loader = ScenarioLoader(scenarios_dir)
        
        tag = metafunc.config.getoption("--tag")
        scenarios = loader.load_scenarios(tag_filter=tag if tag else None)
        
        # ID generation for consistent test names
        ids = [s.get('id', 'unnamed') for s in scenarios]
        
        metafunc.parametrize("scenario", scenarios, ids=ids)

def pytest_sessionfinish(session, exitstatus):
    """Generate meta.json at the end of the session."""
    try:
        from src.utils.meta_info import collect_meta_info
        
        run_folder = _get_run_folder()
        base_reports = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports', run_folder))
        
        # Collect stats
        reporter = session.config.pluginmanager.get_plugin('terminalreporter')
        if reporter:
            passed = len(reporter.stats.get('passed', []))
            failed = len(reporter.stats.get('failed', []))
            skipped = len(reporter.stats.get('skipped', []))
            # Error counts usually in 'error'
            error = len(reporter.stats.get('error', []))
            total = passed + failed + skipped + error
            
            cases_stats = {
                "total": total,
                "passed": passed,
                "failed": failed + error, # Group errors with failed or keep separate? distinct is usually better but user asked for simple
                "skipped": skipped
            }
        else:
            cases_stats = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

        # Artifacts paths relative to project root or just logical paths
        # Relative to project root: reports/RunID/...
        artifacts = {
            "evidence_dir": f"reports/{run_folder}/screenshots/",
            "logs": f"reports/{run_folder}/run_{run_folder}.log",
            "report": f"reports/{run_folder}/report.html"
        }

        meta_data = collect_meta_info(run_folder, cases_stats, artifacts)
        
        meta_json_path = os.path.join(base_reports, 'meta.json')
        import json
        with open(meta_json_path, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, indent=2, ensure_ascii=False)
            
        logging.info(f"Meta JSON generated: {meta_json_path}")
        
    except Exception as e:
        logging.error(f"Failed to generate meta.json: {e}")
