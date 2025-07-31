import requests
import json

def test_chat_api():
    url = "http://localhost:8787/api/chat"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6IjhUTGVrVG1jcXlLek5JcUYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3FwZmxqYmpieXVpeW1lcWdodnN6LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzODc2MzQ3LCJpYXQiOjE3NTM4NzI3NDcsImVtYWlsIjoic2FnbmlrLmJoYXR0YWNoYXJqZWUwOTlAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbCI6InNhZ25pay5iaGF0dGFjaGFyamVlMDk5QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiU2FnbmlrIEdtYWlsIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc1Mzg3Mjc0N31dLCJzZXNzaW9uX2lkIjoiOTQ5OTY4Y2EtNWU1Ny00YjcxLTg3N2UtYTAzNTQ3YzdiNjE2IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.q-_KrojUjmxvTJfXjfi0qnzwTbEcb0RuqVn_lO3IT6Y"
    }
    data = {
        "bot_id": "ab4f29dc-8e15-4f32-bb5c-06df2582a9e9",
        "query": "What services do you offer?",
        "conversation_id": "conv-123456"
    }
    
    try:
        print("Testing chat API with authentication...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! Chat API is working!")
            print(f"Answer: {result.get('answer', 'No answer')}")
            print(f"Sources: {result.get('sources', [])}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API service. Is it running?")
    except requests.exceptions.Timeout:
        print("Error: Request timed out")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat_api() 