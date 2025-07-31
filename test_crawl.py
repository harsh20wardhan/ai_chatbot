#!/usr/bin/env python3

import requests
import json

# Test the crawl API
def test_crawl_api():
    url = "http://localhost:8787/api/crawl/website"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6IjhUTGVrVG1jcXlLek5JcUYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3FwZmxqYmpieXVpeW1lcWdodnN6LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzOTQ1MDExLCJpYXQiOjE3NTM5NDE0MTEsImVtYWlsIjoic2FnbmlrLmJoYXR0YWNoYXJqZWUwOTlAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbCI6InNhZ25pay5iaGF0dGFjaGFyamVlMDk5QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiU2FnbmlrIEdtYWlsIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc1Mzk0MTQxMX1dLCJzZXNzaW9uX2lkIjoiYzZlOThhYmYtMjI2Yy00NTU1LTgxMjctNjc5NzgwOTBlNjNjIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.eQsZPtMg3LxBBrcflZyGVXbtEexAnpGZZ5xN1BdhPXo",
        "Content-Type": "application/json"
    }
    data = {
        "url": "https://example.com",
        "max_pages": 100,
        "max_depth": 3,
        "botId": "40fffdbb-932b-4a2f-aa22-9b004cee27fa"
    }
    
    print("Testing crawl API...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 202:
            print("✅ Crawl API test successful!")
        else:
            print("❌ Crawl API test failed!")
            
    except Exception as e:
        print(f"❌ Error testing crawl API: {e}")

if __name__ == "__main__":
    test_crawl_api() 