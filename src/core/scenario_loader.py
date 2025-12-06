import json
import os
import glob
from typing import List, Dict, Generator

class ScenarioLoader:
    def __init__(self, scenarios_dir: str):
        self.scenarios_dir = scenarios_dir

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
                    
                    # Add file path for reference
                    scenario['_file_path'] = file_path
                    scenarios.append(scenario)

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON {file_path}: {e}")
            except Exception as e:
                print(f"Error loading scenario {file_path}: {e}")
                
        return scenarios
