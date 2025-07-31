#!/usr/bin/env python3

import requests
import json
import time

def test_crawl_apis():
    base_url = "http://localhost:8787/api"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6IjhUTGVrVG1jcXlLek5JcUYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3FwZmxqYmpieXVpeW1lcWdodnN6LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzOTQ1MDExLCJpYXQiOjE3NTM5NDE0MTEsImVtYWlsIjoic2FnbmlrLmJoYXR0YWNoYXJqZWUwOTlAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbCI6InNhZ25pay5iaGF0dGFjaGFyamVlMDk5QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiU2FnbmlrIEdtYWlsIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc1Mzk0MTQxMX1dLCJzZXNzaW9uX2lkIjoiYzZlOThhYmYtMjI2Yy00NTU1LTgxMjctNjc5NzgwOTBlNjNjIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.eQsZPtMg3LxBBrcflZyGVXbtEexAnpGZZ5xN1BdhPXo",
        "Content-Type": "application/json"
    }
    
    bot_id = "40fffdbb-932b-4a2f-aa22-9b004cee27fa"
    
    print("=== Testing All Crawl APIs ===")
    
    # Test 1: Start a crawl job
    print("\n1. Testing POST /api/crawl/website")
    crawl_data = {
        "url": "https://example.com",
        "max_pages": 10,
        "max_depth": 2,
        "botId": bot_id
    }
    
    try:
        response = requests.post(f"{base_url}/crawl/website", headers=headers, json=crawl_data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 202:
            result = response.json()
            job_id = result.get("job_id")
            print(f"✅ Crawl job started successfully! Job ID: {job_id}")
            
            # Test 2: Get crawl status
            print(f"\n2. Testing GET /api/crawl/status/{job_id}")
            try:
                status_response = requests.get(f"{base_url}/crawl/status/{job_id}", headers=headers, timeout=30)
                print(f"Status: {status_response.status_code}")
                print(f"Response: {status_response.text}")
                
                if status_response.status_code == 200:
                    print("✅ Crawl status retrieved successfully!")
                else:
                    print("❌ Failed to get crawl status!")
                    
            except Exception as e:
                print(f"❌ Error getting crawl status: {e}")
            
            # Test 3: Cancel crawl job
            print(f"\n3. Testing DELETE /api/crawl/job/{job_id}")
            try:
                cancel_response = requests.delete(f"{base_url}/crawl/job/{job_id}", headers=headers, timeout=30)
                print(f"Status: {cancel_response.status_code}")
                print(f"Response: {cancel_response.text}")
                
                if cancel_response.status_code == 200:
                    print("✅ Crawl job cancelled successfully!")
                else:
                    print("❌ Failed to cancel crawl job!")
                    
            except Exception as e:
                print(f"❌ Error cancelling crawl job: {e}")
                
        else:
            print("❌ Failed to start crawl job!")
            
    except Exception as e:
        print(f"❌ Error starting crawl job: {e}")
    
    print("\n=== Crawl API Tests Complete ===")

if __name__ == "__main__":
    test_crawl_apis() 