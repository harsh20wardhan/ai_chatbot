import requests
import json

def test_ollama_direct():
    url = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral:7b",
        "prompt": "Hello, how are you?",
        "stream": False
    }
    
    try:
        print("Testing Ollama directly...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Generated text: {result.get('response', 'No response')}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Ollama. Is it running?")
    except requests.exceptions.Timeout:
        print("Error: Request timed out - Ollama might be processing")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ollama_direct() 