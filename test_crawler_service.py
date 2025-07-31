#!/usr/bin/env python3

import requests
import json

# Test the crawler service directly
def test_crawler_service():
    url = "http://localhost:8001/crawl"
    headers = {
        "Authorization": "Bearer your-crawler-secret-key",
        "Content-Type": "application/json"
    }
    data = {
        "url": "https://example.com",
        "max_depth": 3,
        "job_id": "test-job-123",
        "bot_id": "140fffdbb-932b-4a2f-aa22-9b004cee27fa",
        "exclude_patterns": []
    }
    
    print("Testing crawler service directly...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Crawler service test successful!")
        else:
            print("❌ Crawler service test failed!")
            
    except Exception as e:
        print(f"❌ Error testing crawler service: {e}")

# Test if crawler service is running
def test_crawler_health():
    try:
        response = requests.get("http://localhost:8001/", timeout=5)
        print(f"Crawler service health check: {response.status_code}")
        return True
    except Exception as e:
        print(f"Crawler service not accessible: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Crawler Service ===")
    
    # First check if service is running
    if test_crawler_health():
        test_crawler_service()
    else:
        print("❌ Crawler service is not running!")
        print("Please start the crawler service first.") 