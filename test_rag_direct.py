import requests
import json

def test_rag_direct():
    url = "http://localhost:8004/chat"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer your-rag-secret-key"
    }
    data = {
        "query": "What services do you offer?",
        "bot_id": "40fffdbb-932b-4a2f-aa22-9b004cee27fa",
        "conversation_id": "test-conv-123"
    }
    
    try:
        print("Testing RAG service directly...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Answer: {result.get('answer', 'No answer')}")
            print(f"Sources: {result.get('sources', [])}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to RAG service. Is it running?")
    except requests.exceptions.Timeout:
        print("Error: Request timed out - RAG service might be processing")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_rag_direct() 