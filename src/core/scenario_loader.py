import json
import os
import glob
from typing import List, Dict, Generator

class ScenarioLoader:
    def __init__(self, scenarios_dir: str):
        self.scenarios_dir = scenarios_dir
        # Assuming scenarios_shared is at the same level as scenarios directory
        self.shared_scenarios_dir = os.path.abspath(os.path.join(scenarios_dir, '..', 'scenarios_shared'))

    def load_scenarios(self, tag_filter: str = None) -> List[Dict]:
        """Loads all JSON scenarios from the directory recursively."""
        scenarios = []
        pattern = os.path.join(self.scenarios_dir, '**', '*.json')
        
        for file_path in glob.glob(pattern, recursive=True):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Handle both formats:
                # - Recommended: Single scenario object (1 file = 1 scenario)
                # - Legacy: Array of scenarios (for backward compatibility)
                if isinstance(data, dict):
                    # Single scenario object (recommended format)
                    data = [data]
                elif not isinstance(data, list):
                    print(f"Skipping {file_path}: Root content is not a dict or list")
                    continue

                for scenario in data:
                    if tag_filter:
                        tags = scenario.get('tags', [])
                        if tag_filter not in tags:
                            continue
                    
                    # Expand shared scenarios
                    if 'steps' in scenario:
                        scenario['steps'] = self._expand_steps(scenario['steps'])

                    # Add file path for reference
                    scenario['_file_path'] = file_path
                    scenarios.append(scenario)

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON {file_path}: {e}")
            except Exception as e:
                print(f"Error loading scenario {file_path}: {e}")
                
        return scenarios

    def _expand_steps(self, steps: List[Dict]) -> List[Dict]:
        """Recursively expands run_scenario steps."""
        expanded_steps = []
        for step in steps:
            if step.get('type') == 'run_scenario':
                params = step.get('params', {})
                path = params.get('path')
                args = params.get('args')
                
                try:
                    # Load shared scenario steps
                    # Note: We pass the path relative to scenarios_shared
                    shared_steps = self._load_shared_steps(path)
                    
                    # Add variable setting step if args exist
                    if args:
                        set_var_step = {
                            "name": f"Set arguments for {os.path.basename(path)}",
                            "type": "system",
                            "params": {
                                "action": "set_variables",
                                "variables": args
                            },
                            "_source": path  # Attribute to system step too
                        }
                        expanded_steps.append(set_var_step)
                    
                    # Recursively expand the loaded steps (handling nested calls)
                    # Before recursion, mark current steps with source if not already marked?
                    # Actually, let _load_shared_steps or the recursion handle marking.
                    # It is better to attach source here or in _load_shared_steps.
                    # Let's attach source to loaded steps before recursive expansion,
                    # so that even nested expansions carry the info or update it?
                    # If we use recursion:
                    # expanded_child_steps = self._expand_steps(shared_steps)
                    # For each child step, if it doesn't have a source, we might add one?
                    # But actually _load_shared_steps is a leaf loader.
                    
                    # Let's simple tag all loaded steps with the current path
                    for s in shared_steps:
                        if '_source' not in s: 
                             s['_source'] = path
                    
                    # Now recursively expand (if the shared scenario itself calls others)
                    # The recursive call will handle any run_scenario in shared_steps
                    expanded_child_steps = self._expand_steps(shared_steps)
                    
                    expanded_steps.extend(expanded_child_steps)
                    
                except Exception as e:
                    print(f"Error expanding scenario {path}: {e}")
                    raise e
            else:
                expanded_steps.append(step)
        return expanded_steps

    def _load_shared_steps(self, relative_path: str) -> List[Dict]:
        """Loads steps from a shared scenario file."""
        full_path = os.path.join(self.shared_scenarios_dir, relative_path)
        
        # Try appending .json if missing
        if not os.path.exists(full_path) and not full_path.endswith('.json'):
            full_path += '.json'
            
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Shared scenario file not found: {full_path}")
            
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, dict):
            return data.get('steps', [])
        elif isinstance(data, list):
            # If it's a list, assume it is properly a list of steps
            return data
        else:
            raise ValueError(f"Invalid shared scenario format in {full_path}")
