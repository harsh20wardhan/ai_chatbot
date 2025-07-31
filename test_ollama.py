import requests
import os
import json
import time
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
try:
    load_dotenv()
    print("Loaded environment variables")
except Exception as e:
    print(f"Error loading environment variables: {e}")

def test_ollama_connection():
    print("=== OLLAMA CONNECTION TEST ===")
    
    # Get configuration from environment or use defaults
    base_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    if base_url.endswith('/api/generate'):
        base_url = base_url[:-12]
    
    model = os.environ.get("OLLAMA_MODEL", "llama3")
    print(f"Testing connection to Ollama at: {base_url}")
    print(f"Model to test: {model}")
    
    # Step 1: Check if Ollama server is running
    try:
        print(f"Sending request to {base_url}/api/tags...")
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        print(f"Received response with status code: {response.status_code}")
        
        if response.status_code == 200:
            print("\n✅ Ollama server is running")
            models = response.json().get('models', [])
            available_models = [m.get('name') for m in models if m.get('name')]
            print(f"\nAvailable models: {available_models}")
            
            if model in available_models:
                print(f"\n✅ Requested model '{model}' is available")
            else:
                print(f"\n❌ Requested model '{model}' is NOT available")
                print(f"You need to pull the model with: ollama pull {model}")
                return False
        else:
            print(f"\n❌ Ollama server returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"\n❌ Failed to connect to Ollama server: {e}")
        print("\nIs Ollama running? Start it with: ollama serve")
        traceback.print_exc()
        return False
    
    # Step 2: Test model with a simple query
    print("\nTesting model with a simple query...")
    try:
        start_time = time.time()
        print(f"Sending test prompt to {base_url}/api/generate...")
        response = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": "Say hello in one sentence", "stream": False},
            timeout=30
        )
        print(f"Received response with status code: {response.status_code}")
        
        if response.status_code == 200:
            duration = time.time() - start_time
            result = response.json()
            print(f"\n✅ Model test successful ({duration:.2f}s)")
            print(f"Response: {result.get('response')}")
            return True
        else:
            print(f"\n❌ Model test failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"\n❌ Error testing model: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_ollama_connection()
        if success:
            print("\n✅ All tests passed! Your Ollama setup is working correctly.")
        else:
            print("\n❌ Tests failed. Please check the errors above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error running tests: {e}")
        traceback.print_exc()
        sys.exit(1) 