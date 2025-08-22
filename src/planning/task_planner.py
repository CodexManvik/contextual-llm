# Proactive Task Planner
import json
from typing import List, Dict, Any

class ProactivePlanner:
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
    
    def create_plan(self, goal: str) -> List[Dict[str, Any]]:
        prompt = f"Break down this goal into 3-5 actionable steps: {goal}. Return as JSON list of steps."
        response = self.llm_manager.generate_response("You are a task planner.", prompt)
        
        try:
            steps = json.loads(response)
            if isinstance(steps, list):
                return steps
            return []
        except:
            return []
    
    def execute_plan(self, plan: List[Dict[str, Any]], confirmation_callback) -> bool:
        for step in plan:
            if confirmation_callback(step["description"]):
                # Execute step (integrate with system controller)
                print(f"Executing: {step['description']}")
            else:
                return False
        return True
