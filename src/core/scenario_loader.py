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
                    
                # Validate basic structure (can be expanded)
                if not isinstance(data, list):
                     # Assume single scenario object in file, wrap in list if needed or handle accordingly.
                     # Requirements say "Test Scenario File" contains info like id, name, steps.
                     # It implies one scenario per file usually, or a list of scenarios?
                     # Docs 4.2 says "Test Scenario File (XXXX-XXX.json)" holds id, name, steps.
                     # Let's assume the root is a Dictionary representing ONE scenario.
                     if isinstance(data, dict):
                         data = [data]
                     else:
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
