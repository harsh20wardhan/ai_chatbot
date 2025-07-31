import requests
import json

def test_bot_creation():
    url = "http://localhost:8787/api/test/bot"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "name": "Test Bot",
        "description": "A test bot for RAG",
        "website_url": "https://example.com"
    }
    
    try:
        print("Creating test bot...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            bot_id = result.get('bot', {}).get('id')
            print(f"Bot created successfully with ID: {bot_id}")
            return bot_id
        else:
            print(f"Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API service. Is it running?")
        return None
    except requests.exceptions.Timeout:
        print("Error: Request timed out")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    bot_id = test_bot_creation()
    if bot_id:
        print(f"\nUse this bot_id for testing: {bot_id}") 