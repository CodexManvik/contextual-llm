"""
Advanced Command Parser with LLM Integration
Processes natural language commands and extracts structured information
"""

import subprocess
import json
import re
import spacy
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class CommandParser:
    def __init__(self, model_name="qwen2.5:7b"):
        self.model_name = model_name
        self.nlp = spacy.load("en_core_web_sm")
        
        # Load command templates
        self.command_templates = self._load_templates()
        
    def _load_templates(self) -> Dict:
        """Load predefined command templates for quick matching"""
        templates = {
            "whatsapp": {
                "patterns": [
                    "send message to {contact} saying {message}",
                    "message {contact} {message}",
                    "whatsapp {contact} {message}",
                    "text {contact} {message}"
                ],
                "action": "send_message",
                "required_params": ["contact", "message"]
            },
            "system": {
                "patterns": [
                    "open {application}",
                    "launch {application}",
                    "start {application}",
                    "close {application}",
                    "minimize {application}"
                ],
                "action": "app_control",
                "required_params": ["application", "action"]
            },
            "calendar": {
                "patterns": [
                    "schedule meeting with {person} at {time}",
                    "create appointment {title} at {time}",
                    "set reminder {title} for {time}"
                ],
                "action": "calendar_event",
                "required_params": ["title", "time"]
            },
            "browser": {
                "patterns": [
                    "open {website} in browser",
                    "go to {website}",
                    "browse {website}",
                    "search for {query} on google"
                ],
                "action": "browser_action",
                "required_params": ["website"]
            }
        }
        return templates
    
    def parse_command(self, command: str) -> Dict:
        """
        Main parsing function that combines rule-based and LLM approaches
        """
        # First try rule-based parsing for speed
        rule_based_result = self._rule_based_parse(command)
        if rule_based_result["confidence"] > 0.7:
            return rule_based_result
        
        # Fallback to LLM parsing for complex commands
        llm_result = self._llm_parse(command)
        return llm_result
    
    def _rule_based_parse(self, command: str) -> Dict:
        """Fast rule-based parsing for common patterns"""
        command_lower = command.lower().strip()
        
        # List and refresh applications patterns
        if command_lower in ["list applications","list apps","show applications","show apps"]:
            return {
                "intent": "system_control",
                "action": "list_apps",
                "parameters": {},
                "confidence": 0.95,
                "method": "rule_based"
            }
        if command_lower in ["refresh applications","rescan applications","rescan apps","refresh apps"]:
            return {
                "intent": "system_control",
                "action": "refresh_apps",
                "parameters": {},
                "confidence": 0.95,
                "method": "rule_based"
            }
        
        # WhatsApp patterns
        whatsapp_patterns = [
            r"(?:send|message|text|whatsapp)\s+(?:message\s+to\s+)?(\w+)\s+(?:saying\s+)?['\"]?(.+?)['\"]?$",
            r"(?:message|text)\s+(\w+)\s+(.+)$"
        ]
        
        for pattern in whatsapp_patterns:
            match = re.search(pattern, command_lower, re.IGNORECASE)
            if match:
                return {
                    "intent": "whatsapp_send",
                    "action": "send_message",
                    "parameters": {
                        "contact": match.group(1).title(),
                        "message": match.group(2)
                    },
                    "confidence": 0.9,
                    "method": "rule_based"
                }
        
        # System control patterns
        system_patterns = [
            r"(open|launch|start|close|minimize)\s+(.+)$",
        ]
        
        for pattern in system_patterns:
            match = re.search(pattern, command_lower, re.IGNORECASE)
            if match:
                return {
                    "intent": "system_control",
                    "action": "app_control",
                    "parameters": {
                        "action": match.group(1),
                        "application": match.group(2)
                    },
                    "confidence": 0.8,
                    "method": "rule_based"
                }
        
        # Calendar patterns with time extraction
        calendar_patterns = [
            r"(?:schedule|create|set)\s+(?:meeting|appointment|reminder)\s+(?:with\s+)?(.+?)\s+(?:at|for)\s+(.+)$",
        ]
        
        for pattern in calendar_patterns:
            match = re.search(pattern, command_lower, re.IGNORECASE)
            if match:
                time_parsed = self._parse_time(match.group(2))
                return {
                    "intent": "calendar",
                    "action": "create_event",
                    "parameters": {
                        "title": match.group(1),
                        "time": time_parsed
                    },
                    "confidence": 0.8,
                    "method": "rule_based"
                }
        
        return {"confidence": 0.0, "method": "rule_based"}
    
    def _llm_parse(self, command: str) -> Dict:
        """Use LLM for complex command understanding"""
        prompt = f"""
Parse this command and extract the intent and parameters in JSON format.

Command: "{command}"

Available intents:
- whatsapp_send: Send WhatsApp message (needs: contact, message)
- system_control: Control applications (needs: action, application)
- calendar: Calendar operations (needs: title, time)
- browser: Web browsing (needs: website or query)
- unknown: Cannot determine intent

Respond with JSON only:
{{
    "intent": "intent_name",
    "action": "specific_action",
    "parameters": {{"param1": "value1", "param2": "value2"}},
    "confidence": 0.0-1.0
}}
"""
        
        try:
            result = subprocess.run([
                "ollama", "run", self.model_name, prompt
            ], capture_output=True, text=True, timeout=10)
            
            # Extract JSON from response
            response = result.stdout.strip()
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                parsed = json.loads(json_match.group())
                parsed["method"] = "llm"
                return parsed
            else:
                return self._create_unknown_intent(command)
                
        except Exception as e:
            print(f"LLM parsing error: {e}")
            return self._create_unknown_intent(command)
    
    def _parse_time(self, time_str: str) -> str:
        """Parse time expressions into datetime format"""
        now = datetime.now()
        time_str = time_str.lower().strip()
        
        # Common time patterns
        if "tomorrow" in time_str:
            base_date = now + timedelta(days=1)
        elif "today" in time_str:
            base_date = now
        else:
            base_date = now
        
        # Extract time
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', time_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            
            if time_match.group(3) and time_match.group(3).lower() == 'pm' and hour != 12:
                hour += 12
            elif time_match.group(3) and time_match.group(3).lower() == 'am' and hour == 12:
                hour = 0
                
            return base_date.replace(hour=hour, minute=minute).strftime('%Y-%m-%d %H:%M')
        
        return (now + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M')
    
    def _create_unknown_intent(self, command: str) -> Dict:
        """Create unknown intent response"""
        return {
            "intent": "unknown",
            "action": "clarify",
            "parameters": {"original_command": command},
            "confidence": 0.0,
            "method": "fallback"
        }
