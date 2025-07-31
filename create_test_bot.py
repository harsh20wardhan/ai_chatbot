#!/usr/bin/env python3

import requests
import json
import uuid

def create_test_bot():
    url = "http://localhost:8787/api/bots"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6IjhUTGVrVG1jcXlLek5JcUYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3FwZmxqYmpieXVpeW1lcWdodnN6LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzOTQ1MDExLCJpYXQiOjE3NTM5NDE0MTEsImVtYWlsIjoic2FnbmlrLmJoYXR0YWNoYXJqZWUwOTlAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbCI6InNhZ25pay5iaGF0dGFjaGFyamVlMDk5QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiU2FnbmlrIEdtYWlsIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc1Mzk0MTQxMX1dLCJzZXNzaW9uX2lkIjoiYzZlOThhYmYtMjI2Yy00NTU1LTgxMjctNjc5NzgwOTBlNjNjIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.eQsZPtMg3LxBBrcflZyGVXbtEexAnpGZZ5xN1BdhPXo",
        "Content-Type": "application/json"
    }
    data = {
        "name": "Test Bot for Crawling",
        "description": "A test bot for testing crawl functionality",
        "website_url": "https://example.com"
    }
    
    print("Creating test bot...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            bot_id = result.get('id') or result.get('bot', {}).get('id')
            print(f"✅ Test bot created successfully! Bot ID: {bot_id}")
            return bot_id
        else:
            print("❌ Failed to create test bot!")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test bot: {e}")
        return None

def list_bots():
    url = "http://localhost:8787/api/bots"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6IjhUTGVrVG1jcXlLek5JcUYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3FwZmxqYmpieXVpeW1lcWdodnN6LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzOTQ1MDExLCJpYXQiOjE3NTM5NDE0MTEsImVtYWlsIjoic2FnbmlrLmJoYXR0YWNoYXJqZWUwOTlAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbCI6InNhZ25pay5iaGF0dGFjaGFyamVlMDk5QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiU2FnbmlrIEdtYWlsIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIxOTBhYTAyNC02ZDA2LTQwMGMtYmJmZC05MDI4NmYzMzczNjUifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc1Mzk0MTQxMX1dLCJzZXNzaW9uX2lkIjoiYzZlOThhYmYtMjI2Yy00NTU1LTgxMjctNjc5NzgwOTBlNjNjIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.eQsZPtMg3LxBBrcflZyGVXbtEexAnpGZZ5xN1BdhPXo",
        "Content-Type": "application/json"
    }
    
    print("Listing existing bots...")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            bots = result.get('bots', [])
            if bots:
                print("✅ Existing bots:")
                for bot in bots:
                    print(f"  - ID: {bot.get('id')}, Name: {bot.get('name')}")
                return bots[0].get('id') if bots else None
            else:
                print("No existing bots found.")
                return None
        else:
            print("❌ Failed to list bots!")
            return None
            
    except Exception as e:
        print(f"❌ Error listing bots: {e}")
        return None

if __name__ == "__main__":
    print("=== Bot Management Test ===")
    
    # First try to list existing bots
    existing_bot_id = list_bots()
    
    if existing_bot_id:
        print(f"Using existing bot ID: {existing_bot_id}")
    else:
        # Create a new test bot
        new_bot_id = create_test_bot()
        if new_bot_id:
            print(f"Created new bot ID: {new_bot_id}")
        else:
            print("❌ Could not create or find any bots!") 