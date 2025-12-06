from src.core.context import Context
from src.core.execution.runner import Runner

def test_execute_scenario(scenario):
    """
    Main test entry point.
    This function is parametrized by pytest_generate_tests in conftest.py
    """
    context = Context()
    runner = Runner(context)
    runner.execute_scenario(scenario)
