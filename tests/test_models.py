import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from main import AIAssistant
import time
import subprocess
import json


def test_model_performance(model_name, test_prompt="Write a simple Python function to add two numbers"):
    start_time = time.time()
    
    # Run ollama with the test prompt
    result = subprocess.run([
        "ollama", "run", model_name, test_prompt
    ], capture_output=True, text=True, encoding='utf-8', timeout=60)  # <-- Increased timeout here
    
    end_time = time.time()
    response_time = end_time - start_time
    
    print(f"\n{'='*50}")
    print(f"Model: {model_name}")
    print(f"Response Time: {response_time:.2f} seconds")
    print(f"Response: {result.stdout[:200]}...")
    print(f"{'='*50}")
    
    return response_time, result.stdout


# Test all models
models_to_test = [
    "phi3:3.8b",
    "qwen2.5:7b"
]


results = {}
for model in models_to_test:
    try:
        response_time, output = test_model_performance(model)
        results[model] = {
            "response_time": response_time,
            "success": True
        }
        # Wait between tests to avoid overheating
        time.sleep(10)
    except Exception as e:
        results[model] = {
            "error": str(e),
            "success": False
        }
        print(f"Error testing {model}: {e}")


# Print final results
print("\n" + "="*60)
print("FINAL PERFORMANCE COMPARISON")
print("="*60)
for model, result in results.items():
    if result["success"]:
        print(f"{model}: {result['response_time']:.2f}s")
    else:
        print(f"{model}: FAILED - {result.get('error', 'Unknown error')}")
