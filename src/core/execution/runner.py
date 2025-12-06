import logging
import traceback
from datetime import datetime
from typing import Dict, Any

from src.core.context import Context
from src.core.execution.condition import ConditionEvaluator
from src.core.execution.actions.action_dispatcher import ActionDispatcher

class Runner:
    def __init__(self, context: Context):
        self.context = context
        self.condition_evaluator = ConditionEvaluator(context)
        self.dispatcher = ActionDispatcher(context)
        self.logger = logging.getLogger(__name__)

    def execute_scenario(self, scenario: Dict[str, Any]):
        """Executes a single scenario."""
        scenario_name = scenario.get('name', 'Unknown')
        start_time = datetime.now()
        self.logger.info(f"Starting scenario: {scenario_name} at {start_time}")
        
        steps = scenario.get('steps', [])
        
        for i, step in enumerate(steps):
            step_name = step.get('name', f"Step {i+1}")
            self.logger.info(f"  Executing step: {step_name}")
            
            # Check condition
            if 'condition' in step:
                if not self.condition_evaluator.evaluate(step['condition']):
                    self.logger.info(f"    Skipping step '{step_name}' because condition was not met.")
                    continue

            # Execute action
            action_type = step.get('type')
            if not action_type:
                self.logger.error(f"    Step '{step_name}' has no type defined.")
                raise ValueError("Step type is required")

            try:
                # Resolve variables in params
                params = self._resolve_params(step.get('params', {}))
                
                action = self.dispatcher.get_action(action_type)
                action.execute(params)
                
            except Exception as e:
                self.logger.error(f"    Failed step '{step_name}': {e}")
                self.logger.debug(traceback.format_exc())
                raise e

        self.logger.info(f"Finished scenario: {scenario_name}")

    def _resolve_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolves variables in step parameters."""
        resolved = {}
        for k, v in params.items():
            if isinstance(v, str):
                resolved[k] = self.context.resolve(v)
            elif isinstance(v, dict):
                resolved[k] = self._resolve_params(v)
            else:
                resolved[k] = v
        return resolved
