#!/usr/bin/env python3
"""
Test script for document parsing, embedding, and vector storage.
"""

import os
import requests
import json
import uuid
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configuration
PARSER_SERVICE_URL = os.environ.get("PARSER_SERVICE_URL", "http://localhost:8002")
PARSER_SERVICE_KEY = os.environ.get("PARSER_SERVICE_KEY", "your-parser-secret-key")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

def test_parser_connection():
    """Test connection to parser service"""
    try:
        # Just a simple ping to see if the service is up
        response = requests.get(f"{PARSER_SERVICE_URL}/", timeout=5)
        if response.status_code == 404:  # No root endpoint, but service is up
            print("✅ Parser service is running")
            return True
        else:
            print(f"⚠️ Parser service returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to parser service")
        return False
    except Exception as e:
        print(f"❌ Error testing parser connection: {e}")
        return False

def test_document_upload(bot_id, file_path):
    """Test uploading a document to Supabase"""
    try:
        # This would normally be done through the API, but we'll simulate it here
        # In a real scenario, you'd use the Supabase JavaScript client in the frontend
        
        # Generate a document ID
        document_id = str(uuid.uuid4())
        
        print(f"🔄 Testing document upload with file: {file_path}")
        print(f"🔄 Document ID: {document_id}")
        print(f"🔄 Bot ID: {bot_id}")
        
        # Get file details
        file_name = os.path.basename(file_path)
        file_type = file_name.split('.')[-1].lower()
        file_size = os.path.getsize(file_path)
        
        # Simulate the document record creation
        print(f"📄 Document details: {file_name} ({file_type}, {file_size} bytes)")
        
        # Simulate the parser service call
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {PARSER_SERVICE_KEY}"
        }
        
        data = {
            "document_id": document_id,
            "file_path": file_path,
            "file_type": file_type,
            "bot_id": bot_id
        }
        
        print(f"🔄 Calling parser service with data: {json.dumps(data, indent=2)}")
        
        response = requests.post(
            f"{PARSER_SERVICE_URL}/parse",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            print(f"✅ Parser service responded successfully: {response.json()}")
            return True
        else:
            print(f"❌ Parser service error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing document upload: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Starting document parsing tests")
    
    # Test parser connection
    if not test_parser_connection():
        print("❌ Parser service is not available. Exiting.")
        return
    
    # Get bot ID from environment or use a test ID
    bot_id = os.environ.get("TEST_BOT_ID")
    if not bot_id:
        print("⚠️ No TEST_BOT_ID in environment. Using a test ID.")
        bot_id = "test-bot-" + str(uuid.uuid4())
    
    # Test with a sample document
    test_file = os.environ.get("TEST_DOCUMENT_PATH", "parser/test.pdf")
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    test_document_upload(bot_id, test_file)
    
    print("🏁 Document parsing tests completed")

if __name__ == "__main__":
    main()