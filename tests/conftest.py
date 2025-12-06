import sys
import os

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import shutil
import logging
from datetime import datetime

from src.core.context import Context
from src.core.scenario_loader import ScenarioLoader
from src.utils.driver_factory import DriverFactory
from src.core.execution.runner import Runner
from src.utils.screenshot import ScreenshotManager
from src.utils.run_context import get_run_folder_name

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
    
    # 実行ごとの固有フォルダを生成
    run_folder = get_run_folder_name()
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
    
    DriverFactory.close_app()

@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    """Log execution details after collection."""
    logging.info("-" * 40)
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
    """Capture screenshot on failure."""
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
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
            saved_path = manager.capture_screen(filename=filename)
            
            if saved_path:
                print(f"Screenshot saved to {saved_path}")
            else:
                print("Failed to take screenshot.")
        except Exception as e:
            print(f"Failed to take screenshot: {e}")

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
