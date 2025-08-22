# Contextual Memory Manager
from collections import deque
from typing import Dict, List, Any, Optional
import json
import os

class ContextualMemoryManager:
    def __init__(self, persistent_file: str = "memory/persistent_facts.json"):
        self.session_memory: deque = deque(maxlen=50)
        self.persistent_facts: Dict[str, Any] = self._load_persistent(persistent_file)
        self.persistent_file = persistent_file
    
    def _load_persistent(self, file_path: str) -> Dict[str, Any]:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_persistent(self):
        with open(self.persistent_file, 'w', encoding='utf-8') as f:
            json.dump(self.persistent_facts, f, indent=2)
    
    def add_interaction(self, user_input: str, assistant_response: str, actions_taken: List[str]):
        self.session_memory.append({
            "user": user_input,
            "assistant": assistant_response,
            "actions": actions_taken
        })
    
    def add_persistent_fact(self, key: str, value: Any):
        self.persistent_facts[key] = value
        self._save_persistent()
    
    def get_session_summary(self) -> str:
        return "\n".join([f"User: {item['user']}\nAssistant: {item['assistant']}" for item in list(self.session_memory)[-5:]])
    
    def get_persistent_fact(self, key: str) -> Optional[Any]:
        return self.persistent_facts.get(key)
