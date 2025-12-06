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
    
    # Setup Logging
    log_dir = context.get_variable('LOGDIR', 'reports/logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Clean previous screenshots if needed
    screenshot_dir = context.get_variable('SCREENSHOTDIR', 'reports/screenshots')
    if os.path.exists(screenshot_dir):
        # Optional: Clean up or archive. For now just ensure it exists.
        pass
    os.makedirs(screenshot_dir, exist_ok=True)

    yield
    
    # Teardown
    DriverFactory.close_app()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture screenshot on failure."""
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = item.name.replace("/", "_").replace("\\", "_")
            filename = f"reports/screenshots/FAIL_{name}_{timestamp}.png"
            
            # Simple desktop screenshot using Pillow or pywinauto
            # If DriverFactory has an app, maybe take app screenshot, otherwise desktop
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            screenshot.save(filename)
            print(f"Screenshot saved to {filename}")
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
        ids = [s.get('name', 'unnamed') for s in scenarios]
        
        metafunc.parametrize("scenario", scenarios, ids=ids)
