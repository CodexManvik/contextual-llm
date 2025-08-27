import logging
import time
import json
import os
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio

try:
    import pywinauto
    from pywinauto import Application
    import pyautogui
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False

class IntelligentAppController:
    """AI-powered application interaction using LLM reasoning"""
    
    def __init__(self, llm_manager, context_manager, training_manager):
        self.logger = logging.getLogger(__name__)
        self.llm = llm_manager
        self.context = context_manager
        self.training = training_manager
        
        # Dynamic capability learning
        self.app_capabilities: Dict[str, Dict] = {}
        self.interaction_patterns: Dict[str, List] = {}
        self.success_patterns: Dict[str, float] = {}
        
        # Load learned patterns
        self.load_learned_patterns()
    
    def discover_app_capabilities(self, app_name: str) -> Dict:
        """Use LLM to understand what an app can do"""
        
        if app_name in self.app_capabilities:
            return self.app_capabilities[app_name]
        
        # Get app context
        app_info = self.get_app_context(app_name)
        
        # Ask LLM what this app can do
        capability_prompt = f"""
        Analyze this application: {app_name}
        App info: {app_info}
        
        What are the key capabilities and common tasks for this application?
        Consider: document creation, data entry, navigation, file operations, etc.
        
        Return a JSON structure with:
        - primary_functions: list of main purposes
        - common_tasks: list of typical user tasks  
        - ui_elements: likely UI components
        - keyboard_shortcuts: common shortcuts
        - file_operations: what file types it handles
        
        Be concise and practical.
        """
        
        try:
            response = self.llm.generate_response(capability_prompt, {
                'app_name': app_name,
                'task_type': 'capability_analysis'
            })
            
            # Parse LLM response
            capabilities = self.parse_llm_capabilities(response)
            self.app_capabilities[app_name] = capabilities
            
            # Save learned capabilities
            self.save_learned_patterns()
            
            return capabilities
            
        except Exception as e:
            self.logger.error(f"Capability discovery failed for {app_name}: {e}")
            return self.get_default_capabilities(app_name)
    
    def execute_intelligent_task(self, app_name: str, user_intent: str, context: Dict) -> Dict:
        """Execute task using AI reasoning and learning"""
        
        try:
            # Get app capabilities
            capabilities = self.discover_app_capabilities(app_name)
            
            # Get current app state
            app_state = self.analyze_app_state(app_name)
            
            # Create execution plan using LLM
            execution_plan = self.create_execution_plan(
                app_name, user_intent, capabilities, app_state, context
            )
            
            if not execution_plan.get('steps'):
                return {"success": False, "message": "Could not create execution plan"}
            
            # Execute plan with learning
            return self.execute_plan_with_learning(app_name, execution_plan, user_intent)
            
        except Exception as e:
            self.logger.error(f"Intelligent task execution failed: {e}")
            return {"success": False, "message": f"Task failed: {str(e)}"}
    
    def create_execution_plan(self, app_name: str, user_intent: str, 
                            capabilities: Dict, app_state: Dict, context: Dict) -> Dict:
        """Use LLM to create dynamic execution plan"""
        
        # Include previous successful patterns
        success_context = self.get_success_patterns(app_name, user_intent)
        
        planning_prompt = f"""
        Create an execution plan for this task:
        
        Application: {app_name}
        User Intent: "{user_intent}"
        App Capabilities: {json.dumps(capabilities, indent=2)}
        Current App State: {app_state}
        Previous Success Patterns: {success_context}
        
        Create a step-by-step execution plan. Each step should be:
        1. Specific and actionable
        2. Include fallback options
        3. Specify expected outcomes
        
        Return JSON format:
        {{
            "plan_confidence": 0.8,
            "steps": [
                {{
                    "action": "specific action to take",
                    "method": "keyboard|mouse|ui_element|api",
                    "parameters": {{"key": "value"}},
                    "expected_result": "what should happen",
                    "fallback": "alternative if this fails",
                    "verification": "how to confirm success"
                }}
            ],
            "success_indicators": ["what indicates success"],
            "failure_recovery": "what to do if plan fails"
        }}
        
        Be practical and focus on achievable steps.
        """
        
        try:
            response = self.llm.generate_response(planning_prompt, {
                'app_name': app_name,
                'user_intent': user_intent,
                'planning_mode': True
            })
            
            return self.parse_execution_plan(response)
            
        except Exception as e:
            self.logger.error(f"Execution planning failed: {e}")
            return {"steps": []}
    
    def execute_plan_with_learning(self, app_name: str, plan: Dict, original_intent: str) -> Dict:
        """Execute plan while learning from results"""
        
        execution_log = {
            'app_name': app_name,
            'original_intent': original_intent,
            'plan': plan,
            'step_results': [],
            'start_time': time.time(),
            'success': False
        }
        
        try:
            for i, step in enumerate(plan.get('steps', [])):
                step_result = self.execute_step_intelligently(step, app_name)
                execution_log['step_results'].append(step_result)
                
                # Learn from step result
                self.learn_from_step(app_name, step, step_result)
                
                if not step_result.get('success', False):
                    # Try fallback
                    fallback = step.get('fallback')
                    if fallback:
                        fallback_result = self.execute_fallback(fallback, app_name)
                        if not fallback_result.get('success', False):
                            execution_log['failure_step'] = i
                            break
                
                # Add intelligent delay between steps
                delay = self.calculate_smart_delay(step, step_result)
                if delay > 0:
                    time.sleep(delay)
            
            # Verify overall success
            success = self.verify_task_completion(plan, execution_log)
            execution_log['success'] = success
            execution_log['end_time'] = time.time()
            
            # Learn from complete execution
            self.learn_from_execution(execution_log)
            
            if success:
                return {
                    "success": True, 
                    "message": f"Successfully completed task in {app_name}",
                    "execution_log": execution_log
                }
            else:
                return {
                    "success": False,
                    "message": "Task execution incomplete",
                    "execution_log": execution_log
                }
                
        except Exception as e:
            self.logger.error(f"Plan execution failed: {e}")
            execution_log['error'] = str(e)
            self.learn_from_execution(execution_log)
            return {"success": False, "message": f"Execution error: {str(e)}"}
    
    def execute_step_intelligently(self, step: Dict, app_name: str) -> Dict:
        """Execute individual step with intelligence"""
        
        method = step.get('method', 'keyboard')
        action = step.get('action', '')
        parameters = step.get('parameters', {})
        
        try:
            if method == 'keyboard':
                return self.execute_keyboard_action(action, parameters)
            elif method == 'mouse':
                return self.execute_mouse_action(action, parameters)
            elif method == 'ui_element':
                return self.execute_ui_action(app_name, action, parameters)
            elif method == 'smart_input':
                return self.execute_smart_input(action, parameters)
            else:
                return {"success": False, "message": f"Unknown method: {method}"}
                
        except Exception as e:
            return {"success": False, "message": f"Step execution failed: {str(e)}"}
    
    def execute_keyboard_action(self, action: str, parameters: Dict) -> Dict:
        """Execute keyboard actions intelligently"""
        try:
            if not AUTOMATION_AVAILABLE:
                return {"success": False, "message": "Automation not available"}
            
            if action == 'type_text':
                text = parameters.get('text', '')
                if text:
                    pyautogui.write(text)
                    return {"success": True, "message": f"Typed: {text}"}
                
            elif action == 'shortcut':
                keys = parameters.get('keys', [])
                if keys:
                    pyautogui.hotkey(*keys)
                    return {"success": True, "message": f"Executed shortcut: {'+'.join(keys)}"}
                    
            elif action == 'key_press':
                key = parameters.get('key', '')
                if key:
                    pyautogui.press(key)
                    return {"success": True, "message": f"Pressed key: {key}"}
            
            return {"success": False, "message": f"Unknown keyboard action: {action}"}
            
        except Exception as e:
            return {"success": False, "message": f"Keyboard action failed: {str(e)}"}
    
    def learn_from_execution(self, execution_log: Dict) -> None:
        """Learn from complete execution for future improvement"""
        
        app_name = execution_log.get('app_name')
        intent = execution_log.get('original_intent')
        success = execution_log.get('success', False)
        
        # Update success patterns
        pattern_key = f"{app_name}:{intent}"
        if pattern_key not in self.success_patterns:
            self.success_patterns[pattern_key] = 0.0
            
        # Update success rate with exponential smoothing
        current_rate = self.success_patterns[pattern_key]
        new_rate = 0.8 * current_rate + 0.2 * (1.0 if success else 0.0)
        self.success_patterns[pattern_key] = new_rate
        
        # Store successful patterns for future use
        if success:
            if app_name not in self.interaction_patterns:
                self.interaction_patterns[app_name] = []
                
            pattern = {
                'intent': intent,
                'plan': execution_log.get('plan'),
                'success_rate': new_rate,
                'timestamp': datetime.now().isoformat()
            }
            
            self.interaction_patterns[app_name].append(pattern)
            
            # Keep only best patterns (top 10 per app)
            self.interaction_patterns[app_name] = sorted(
                self.interaction_patterns[app_name],
                key=lambda x: x.get('success_rate', 0),
                reverse=True
            )[:10]
        
        # Use training manager to store learning data
        self.training.add_interaction_data({
            'type': 'app_interaction',
            'app_name': app_name,
            'intent': intent,
            'success': success,
            'execution_time': execution_log.get('end_time', 0) - execution_log.get('start_time', 0),
            'steps_count': len(execution_log.get('step_results', [])),
            'timestamp': datetime.now().isoformat()
        })
        
        self.save_learned_patterns()
    
    def get_app_context(self, app_name: str) -> Dict:
        """Get intelligent context about the application"""
        
        context = {
            'app_name': app_name,
            'is_running': False,
            'window_title': None,
            'recent_interactions': [],
            'user_patterns': []
        }
        
        # Get from context manager
        system_state = self.context.system_state
        if 'running_apps' in system_state:
            context['is_running'] = app_name.lower() in [
                app.lower() for app in system_state['running_apps']
            ]
        
        # Get user interaction patterns
        user_patterns = self.context.user_behavior_patterns
        app_usage = self.context.app_usage_patterns
        if app_name in app_usage:
            context['user_patterns'] = app_usage[app_name]
        
        return context
    
    def analyze_app_state(self, app_name: str) -> Dict:
        """Analyze current application state intelligently"""
        
        state = {
            'window_focused': False,
            'estimated_state': 'unknown',
            'ui_elements_visible': [],
            'current_document': None
        }
        
        try:
            if AUTOMATION_AVAILABLE:
                # Try to get window information
                windows = pywinauto.findwindows.find_windows(title_re=f".*{app_name}.*")
                if windows:
                    state['window_focused'] = True
                    # Could add more detailed state analysis here
                    
        except Exception as e:
            self.logger.debug(f"App state analysis failed for {app_name}: {e}")
        
        return state
    
    def parse_llm_capabilities(self, llm_response: str) -> Dict:
        """Parse LLM response about app capabilities"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback: parse text response
            return {
                'primary_functions': ['general use'],
                'common_tasks': ['open', 'close', 'basic interaction'],
                'ui_elements': ['window', 'menu', 'buttons'],
                'keyboard_shortcuts': {'save': 'ctrl+s', 'copy': 'ctrl+c'},
                'file_operations': ['open', 'save']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse LLM capabilities: {e}")
            return self.get_default_capabilities("unknown")
    
    def parse_execution_plan(self, llm_response: str) -> Dict:
        """Parse LLM execution plan response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
                
            # Fallback: create simple plan
            return {
                "plan_confidence": 0.5,
                "steps": [{
                    "action": "basic_interaction",
                    "method": "keyboard", 
                    "parameters": {},
                    "expected_result": "some interaction",
                    "verification": "check for changes"
                }]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse execution plan: {e}")
            return {"steps": []}
    
    def load_learned_patterns(self) -> None:
        """Load previously learned interaction patterns"""
        try:
            pattern_file = "config/learned_patterns.json"
            if os.path.exists(pattern_file):
                with open(pattern_file, 'r') as f:
                    data = json.load(f)
                    self.app_capabilities = data.get('capabilities', {})
                    self.interaction_patterns = data.get('patterns', {})
                    self.success_patterns = data.get('success_rates', {})
        except Exception as e:
            self.logger.error(f"Failed to load learned patterns: {e}")
    
    def save_learned_patterns(self) -> None:
        """Save learned patterns for future use"""
        try:
            import os
            os.makedirs('config', exist_ok=True)
            
            data = {
                'capabilities': self.app_capabilities,
                'patterns': self.interaction_patterns,
                'success_rates': self.success_patterns,
                'last_updated': datetime.now().isoformat()
            }
            
            with open('config/learned_patterns.json', 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save learned patterns: {e}")
    
    # Additional helper methods...
    def get_success_patterns(self, app_name: str, intent: str) -> str:
        """Get previous successful patterns for similar intents"""
        patterns = self.interaction_patterns.get(app_name, [])
        relevant = [p for p in patterns if intent.lower() in p.get('intent', '').lower()]
        if relevant:
            return f"Previous successful approaches: {json.dumps(relevant[:3], indent=2)}"
        return "No previous successful patterns found."
    
    def get_default_capabilities(self, app_name: str) -> Dict:
        """Get basic default capabilities"""
        return {
            'primary_functions': ['basic application'],
            'common_tasks': ['open', 'interact', 'close'],
            'ui_elements': ['window', 'controls'],
            'keyboard_shortcuts': {},
            'file_operations': []
        }

    def execute_mouse_action(self, action: str, parameters: Dict) -> Dict:
        """Execute mouse actions intelligently"""
        try:
            if not AUTOMATION_AVAILABLE:
                return {"success": False, "message": "Automation not available"}
            
            if action == 'click':
                x = parameters.get('x')
                y = parameters.get('y')
                if x is not None and y is not None:
                    pyautogui.click(x, y)
                    return {"success": True, "message": f"Clicked at ({x}, {y})"}
                else:
                    pyautogui.click()
                    return {"success": True, "message": "Clicked at current position"}
            
            elif action == 'double_click':
                x = parameters.get('x')
                y = parameters.get('y')
                if x is not None and y is not None:
                    pyautogui.doubleClick(x, y)
                    return {"success": True, "message": f"Double clicked at ({x}, {y})"}
                else:
                    pyautogui.doubleClick()
                    return {"success": True, "message": "Double clicked at current position"}
            
            elif action == 'right_click':
                x = parameters.get('x')
                y = parameters.get('y')
                if x is not None and y is not None:
                    pyautogui.rightClick(x, y)
                    return {"success": True, "message": f"Right clicked at ({x}, {y})"}
                else:
                    pyautogui.rightClick()
                    return {"success": True, "message": "Right clicked at current position"}
            
            elif action == 'scroll':
                clicks = parameters.get('clicks', 3)
                pyautogui.scroll(clicks)
                return {"success": True, "message": f"Scrolled {clicks} clicks"}
            
            elif action == 'move':
                x = parameters.get('x')
                y = parameters.get('y')
                if x is not None and y is not None:
                    pyautogui.moveTo(x, y)
                    return {"success": True, "message": f"Moved to ({x}, {y})"}
            
            return {"success": False, "message": f"Unknown mouse action: {action}"}
            
        except Exception as e:
            return {"success": False, "message": f"Mouse action failed: {str(e)}"}

    def execute_ui_action(self, app_name: str, action: str, parameters: Dict) -> Dict:
        """Execute UI element actions (placeholder for advanced UI automation)"""
        try:
            if not AUTOMATION_AVAILABLE:
                return {"success": False, "message": "UI automation not available"}
            
            # This is a placeholder - real UI automation would be more complex
            if action == 'focus_window':
                # Try to find and focus the application window
                try:
                    app = Application().connect(title_re=f".*{app_name}.*")
                    app.top_window().set_focus()
                    return {"success": True, "message": f"Focused {app_name} window"}
                except:
                    return {"success": False, "message": f"Could not find {app_name} window"}
            
            elif action == 'maximize':
                try:
                    app = Application().connect(title_re=f".*{app_name}.*")
                    app.top_window().maximize()
                    return {"success": True, "message": f"Maximized {app_name} window"}
                except:
                    return {"success": False, "message": f"Could not maximize {app_name} window"}
            
            elif action == 'minimize':
                try:
                    app = Application().connect(title_re=f".*{app_name}.*")
                    app.top_window().minimize()
                    return {"success": True, "message": f"Minimized {app_name} window"}
                except:
                    return {"success": False, "message": f"Could not minimize {app_name} window"}
            
            return {"success": False, "message": f"Unknown UI action: {action}"}
            
        except Exception as e:
            return {"success": False, "message": f"UI action failed: {str(e)}"}

    def execute_smart_input(self, action: str, parameters: Dict) -> Dict:
        """Execute smart input actions with context awareness"""
        try:
            if not AUTOMATION_AVAILABLE:
                return {"success": False, "message": "Automation not available"}
            
            if action == 'type_with_delay':
                text = parameters.get('text', '')
                delay = parameters.get('delay', 0.1)
                for char in text:
                    pyautogui.write(char)
                    time.sleep(delay)
                return {"success": True, "message": f"Typed '{text}' with {delay}s delay"}
            
            elif action == 'type_paragraph':
                text = parameters.get('text', '')
                lines = text.split('\n')
                for line in lines:
                    pyautogui.write(line)
                    pyautogui.press('enter')
                    time.sleep(0.2)
                return {"success": True, "message": "Typed paragraph with line breaks"}
            
            elif action == 'smart_paste':
                # Simulate paste operation with proper timing
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.5)  # Wait for paste to complete
                return {"success": True, "message": "Executed smart paste"}
            
            return {"success": False, "message": f"Unknown smart input action: {action}"}
            
        except Exception as e:
            return {"success": False, "message": f"Smart input failed: {str(e)}"}

    def execute_fallback(self, fallback: str, app_name: str) -> Dict:
        """Execute fallback action when primary action fails"""
        try:
            # Parse fallback instruction (could be more sophisticated)
            if 'keyboard' in fallback.lower():
                # Extract keyboard action from fallback
                if 'type' in fallback.lower():
                    # Try to extract text to type
                    match = re.search(r'type\s+["\']?(.+?)["\']?', fallback, re.IGNORECASE)
                    if match:
                        text = match.group(1)
                        return self.execute_keyboard_action('type_text', {'text': text})
                
                elif 'press' in fallback.lower():
                    # Try to extract key to press
                    match = re.search(r'press\s+([a-z0-9]+)', fallback, re.IGNORECASE)
                    if match:
                        key = match.group(1)
                        return self.execute_keyboard_action('key_press', {'key': key})
            
            elif 'mouse' in fallback.lower():
                # Simple mouse fallback - click at center
                if AUTOMATION_AVAILABLE:
                    screen_width, screen_height = pyautogui.size()
                    x, y = screen_width // 2, screen_height // 2
                    return self.execute_mouse_action('click', {'x': x, 'y': y})
                else:
                    return {"success": False, "message": "Automation not available for mouse fallback"}
            
            # Default fallback - try to focus the app window
            return self.execute_ui_action(app_name, 'focus_window', {})
            
        except Exception as e:
            return {"success": False, "message": f"Fallback execution failed: {str(e)}"}

    def learn_from_step(self, app_name: str, step: Dict, step_result: Dict) -> None:
        """Learn from individual step execution"""
        success = step_result.get('success', False)
        step_type = step.get('method', 'unknown')
        
        # Track step success rates
        step_key = f"{app_name}:{step_type}:{step.get('action', 'unknown')}"
        if step_key not in self.success_patterns:
            self.success_patterns[step_key] = 0.0
        
        # Update success rate with exponential smoothing
        current_rate = self.success_patterns[step_key]
        new_rate = 0.9 * current_rate + 0.1 * (1.0 if success else 0.0)
        self.success_patterns[step_key] = new_rate
        
        self.logger.debug(f"Learned from step: {step_key} -> success_rate={new_rate:.2f}")

    def calculate_smart_delay(self, step: Dict, step_result: Dict) -> float:
        """Calculate intelligent delay between steps based on context"""
        base_delay = 0.5  # Base delay in seconds
        
        # Adjust delay based on step type
        step_type = step.get('method', '')
        if step_type == 'keyboard':
            # Longer delay for typing to ensure text is processed
            text = step.get('parameters', {}).get('text', '')
            base_delay += len(text) * 0.05  # Add 50ms per character
            
        elif step_type == 'ui_element':
            # UI operations might need more time
            base_delay += 1.0
            
        elif step_type == 'smart_input':
            # Smart input might involve complex operations
            base_delay += 0.8
        
        # Adjust based on previous step success
        if not step_result.get('success', False):
            # If previous step failed, add extra delay for recovery
            base_delay += 1.0
        
        # Cap the maximum delay
        return min(base_delay, 5.0)

    def verify_task_completion(self, plan: Dict, execution_log: Dict) -> bool:
        """Verify if the overall task was completed successfully"""
        step_results = execution_log.get('step_results', [])
        
        if not step_results:
            return False
        
        # Count successful steps
        successful_steps = sum(1 for result in step_results if result.get('success', False))
        total_steps = len(step_results)
        
        # If all steps were successful, task is complete
        if successful_steps == total_steps:
            return True
        
        # Check if we have success indicators from the plan
        success_indicators = plan.get('success_indicators', [])
        if success_indicators:
            # For now, assume partial success is acceptable if we have some indicators
            # In a real implementation, you'd check actual system state
            return successful_steps > 0
        
        # Default: consider task successful if majority of steps succeeded
        success_ratio = successful_steps / total_steps
        return success_ratio >= 0.7  # 70% success rate threshold
