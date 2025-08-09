import subprocess
import time
import json

class AIAssistantPhase1:
    def __init__(self, model_name="qwen2.5:7b"):
        self.model_name = model_name
        print(f"Initializing AI Assistant with model: {model_name}")
    
    def send_to_llm(self, prompt):
        """Send prompt to LLM and get response"""
        try:
            result = subprocess.run([
                "ollama", "run", self.model_name, prompt
            ], capture_output=True, text=True, timeout=30)
            
            return result.stdout.strip()
        except Exception as e:
            return f"Error: {e}"
    
    def test_basic_intelligence(self):
        """Test basic AI capabilities"""
        test_prompts = [
            "What is 2+2?",
            "Write a simple 'hello world' in Python",
            "Explain what you can help me with in one sentence"
        ]
        
        print("\n" + "="*50)
        print("TESTING AI INTELLIGENCE")
        print("="*50)
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\nTest {i}: {prompt}")
            print("-" * 30)
            
            start_time = time.time()
            response = self.send_to_llm(prompt)
            response_time = time.time() - start_time
            
            print(f"Response ({response_time:.2f}s): {response[:200]}...")
    
    def test_system_command_understanding(self):
        """Test if AI can understand system commands"""
        system_prompts = [
            "If I wanted to open WhatsApp Web, what steps would I need to take?",
            "How would I schedule a meeting in Windows Calendar?",
            "What's the process to send a message to someone?"
        ]
        
        print("\n" + "="*50)
        print("TESTING SYSTEM COMMAND UNDERSTANDING")
        print("="*50)
        
        for i, prompt in enumerate(system_prompts, 1):
            print(f"\nSystem Test {i}: {prompt}")
            print("-" * 40)
            
            response = self.send_to_llm(prompt)
            print(f"AI Response: {response[:300]}...")

def main():
    print("AI ASSISTANT - PHASE 1 INTEGRATION TEST")
    print("="*60)
    
    # Test different models
    models_to_test = ["qwen2.5:7b", "phi3:3.8b"]
    
    for model in models_to_test:
        try:
            print(f"\n{'='*60}")
            print(f"TESTING MODEL: {model}")
            print(f"{'='*60}")
            
            assistant = AIAssistantPhase1(model)
            assistant.test_basic_intelligence()
            assistant.test_system_command_understanding()
            
        except Exception as e:
            print(f"Error testing {model}: {e}")
    
    print("\n" + "="*60)
    print("PHASE 1 TESTING COMPLETE!")
    print("="*60)
    
    print("\nNext Steps:")
    print("1. Choose your preferred model based on performance")
    print("2. Proceed to Phase 2: System Integration")
    print("3. Start building the voice command interface")

if __name__ == "__main__":
    main()
