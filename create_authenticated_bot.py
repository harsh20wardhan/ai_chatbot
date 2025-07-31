import requests
import json
import uuid

def create_authenticated_bot():
    # Create a test bot using the authenticated API
    bot_id = str(uuid.uuid4())
    
    url = "http://localhost:8787/api/bots"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6IjhUTGVrVG1jcXlLek5JcUYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3FwZmxqYmpieXVpeW1lcWdodnN6LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzODc2MzQ3LCJpYXQiOjE3NTM4NzI3NDcsImVtYWlsIjoic2FnbmlrLmJoYXR0YWNoYXJqZWUwOTlAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbCI6InNhZ25pay5iaGF0dGFjaGFyamVlMDk5QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiU2FnbmlrIEdtYWlsIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc1Mzg3Mjc0N31dLCJzZXNzaW9uX2lkIjoiOTQ5OTY4Y2EtNWU1Ny00YjcxLTg3N2UtYTAzNTQ3YzdiNjE2IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.q-_KrojUjmxvTJfXjfi0qnzwTbEcb0RuqVn_lO3IT6Y"
    }
    data = {
        "name": "Test Bot",
        "description": "A test bot for RAG",
        "website_url": "https://example.com"
    }
    
    try:
        print("Creating authenticated test bot...")
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
    bot_id = create_authenticated_bot()
    if bot_id:
        print(f"\nUse this bot_id for testing: {bot_id}")
        
        # Test the bot immediately
        print("\nTesting the bot...")
        test_data = {
            "bot_id": bot_id,
            "query": "What services do you offer?",
            "conversation_id": "conv-123456"
        }
        
        test_url = "http://localhost:8787/api/chat"
        test_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6IjhUTGVrVG1jcXlLek5JcUYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3FwZmxqYmpieXVpeW1lcWdodnN6LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzODc2MzQ3LCJpYXQiOjE3NTM4NzI3NDcsImVtYWlsIjoic2FnbmlrLmJoYXR0YWNoYXJqZWUwOTlAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbCI6InNhZ25pay5iaGF0dGFjaGFyamVlMDk5QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiU2FnbmlrIEdtYWlsIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc1Mzg3Mjc0N31dLCJzZXNzaW9uX2lkIjoiOTQ5OTY4Y2EtNWU1Ny00YjcxLTg3N2UtYTAzNTQ3YzdiNjE2IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.q-_KrojUjmxvTJfXjfi0qnzwTbEcb0RuqVn_lO3IT6Y"
        }
        
        try:
            response = requests.post(test_url, headers=test_headers, json=test_data, timeout=60)
            print(f"Test Status Code: {response.status_code}")
            print(f"Test Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS! Chat API is working!")
                print(f"Answer: {result.get('answer', 'No answer')}")
                print(f"Sources: {result.get('sources', [])}")
            else:
                print(f"❌ Chat API test failed: {response.text}")
        except Exception as e:
            print(f"Test Error: {e}") 