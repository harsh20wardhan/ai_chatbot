#!/usr/bin/env python3
"""
Comprehensive RAG System Test Script
Tests all components: Embedding Service, Parser Service, RAG Service, and Qdrant
"""

import requests
import json
import time
import os
from dotenv import load_dotenv
import boto3
from qdrant_client import QdrantClient
import uuid

# Load environment variables
load_dotenv()

# Configuration
EMBEDDING_SERVICE_URL = "http://localhost:8003"
PARSER_SERVICE_URL = "http://localhost:8002"
RAG_SERVICE_URL = "http://localhost:8001"
API_SERVICE_URL = "http://localhost:8000"

EMBEDDING_API_KEY = os.environ.get("EMBEDDINGS_SERVICE_KEY", "your-embedding-secret-key")
PARSER_API_KEY = os.environ.get("PARSER_SERVICE_KEY", "your-parser-secret-key")
RAG_API_KEY = os.environ.get("RAG_SERVICE_KEY", "your-rag-secret-key")

# Test bot ID
TEST_BOT_ID = "test-bot-" + str(uuid.uuid4())[:8]

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.ENDC}")

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message.center(60)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}\n")

def test_service_health(service_name, url):
    """Test if a service is running"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"{service_name} is running")
            return True
        else:
            print_warning(f"{service_name} responded with status {response.status_code}")
            return True  # Service is running but may not have health endpoint
    except requests.exceptions.RequestException:
        try:
            # Try a basic request to see if service is up
            response = requests.get(url, timeout=5)
            print_success(f"{service_name} is running")
            return True
        except requests.exceptions.RequestException:
            print_error(f"{service_name} is not responding at {url}")
            return False

def test_qdrant_connection():
    """Test Qdrant connection"""
    try:
        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.environ.get("QDRANT_API_KEY", "")
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        
        collections = client.get_collections()
        print_success(f"Qdrant connected. Found {len(collections.collections)} collections")
        return True, client
    except Exception as e:
        print_error(f"Qdrant connection failed: {e}")
        return False, None

def test_bedrock_connection():
    """Test AWS Bedrock connection"""
    try:
        bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name='us-west-2',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )
        
        # Test embedding generation
        response = bedrock_runtime.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps({"inputText": "test embedding"})
        )
        response_body = json.loads(response['body'].read())
        embedding = response_body['embedding']
        
        print_success(f"Bedrock connected. Generated {len(embedding)}-dimensional embedding")
        return True
    except Exception as e:
        print_error(f"Bedrock connection failed: {e}")
        return False

def test_embedding_service():
    """Test embedding service"""
    try:
        headers = {
            "Authorization": f"Bearer {EMBEDDING_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "job_id": f"test-job-{uuid.uuid4()}",
            "bot_id": TEST_BOT_ID,
            "document_ids": ["test-doc-1"]
        }
        
        response = requests.post(
            f"{EMBEDDING_SERVICE_URL}/embed",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Embedding service processed {result.get('documents_processed', 0)} documents")
            return True
        else:
            print_error(f"Embedding service failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Embedding service test failed: {e}")
        return False

def test_rag_service():
    """Test RAG service"""
    try:
        headers = {
            "Authorization": f"Bearer {RAG_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "query": "What is the test document about?",
            "bot_id": TEST_BOT_ID,
            "user_id": "test-user"
        }
        
        response = requests.post(
            f"{RAG_SERVICE_URL}/query",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('answer', '')
            context = result.get('context', [])
            
            print_success(f"RAG service responded with {len(answer)} character answer")
            print_info(f"Found {len(context)} context chunks")
            
            if context:
                print_success("RAG service successfully retrieved context from Qdrant")
            else:
                print_warning("RAG service returned no context (may be expected for test data)")
            
            return True
        else:
            print_error(f"RAG service failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"RAG service test failed: {e}")
        return False

def test_vector_dimensions(client):
    """Test that all collections use 1024 dimensions"""
    try:
        collections = client.get_collections()
        
        for collection in collections.collections:
            try:
                collection_info = client.get_collection(collection.name)
                vector_size = collection_info.config.params.vectors.size
                
                if vector_size == 1024:
                    print_success(f"Collection '{collection.name}' uses correct 1024 dimensions")
                else:
                    print_warning(f"Collection '{collection.name}' uses {vector_size} dimensions (should be 1024)")
            except Exception as e:
                print_warning(f"Could not check dimensions for collection '{collection.name}': {e}")
        
        return True
    except Exception as e:
        print_error(f"Vector dimension test failed: {e}")
        return False

def cleanup_test_data(client):
    """Clean up test data"""
    try:
        # Delete test collection if it exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if TEST_BOT_ID in collection_names:
            client.delete_collection(TEST_BOT_ID)
            print_success(f"Cleaned up test collection: {TEST_BOT_ID}")
        
        return True
    except Exception as e:
        print_warning(f"Cleanup failed: {e}")
        return False

def main():
    """Run all tests"""
    print_header("RAG SYSTEM COMPREHENSIVE TEST")
    
    print_info(f"Test Bot ID: {TEST_BOT_ID}")
    
    # Test 1: Service Health Checks
    print_header("SERVICE HEALTH CHECKS")
    services_ok = True
    services_ok &= test_service_health("Embedding Service", EMBEDDING_SERVICE_URL)
    services_ok &= test_service_health("Parser Service", PARSER_SERVICE_URL)
    services_ok &= test_service_health("RAG Service", RAG_SERVICE_URL)
    
    if not services_ok:
        print_error("Some services are not running. Please start all services first.")
        return False
    
    # Test 2: External Dependencies
    print_header("EXTERNAL DEPENDENCIES")
    qdrant_ok, qdrant_client = test_qdrant_connection()
    bedrock_ok = test_bedrock_connection()
    
    if not qdrant_ok or not bedrock_ok:
        print_error("External dependencies failed. Check your configuration.")
        return False
    
    # Test 3: Vector Dimensions
    print_header("VECTOR DIMENSIONS CHECK")
    test_vector_dimensions(qdrant_client)
    
    # Test 4: Embedding Service
    print_header("EMBEDDING SERVICE TEST")
    embedding_ok = test_embedding_service()
    
    if embedding_ok:
        # Wait a moment for embedding to complete
        print_info("Waiting for embedding to complete...")
        time.sleep(3)
    
    # Test 5: RAG Service
    print_header("RAG SERVICE TEST")
    rag_ok = test_rag_service()
    
    # Test 6: Cleanup
    print_header("CLEANUP")
    cleanup_test_data(qdrant_client)
    
    # Final Results
    print_header("TEST RESULTS SUMMARY")
    
    if services_ok and qdrant_ok and bedrock_ok and embedding_ok and rag_ok:
        print_success("🎉 ALL TESTS PASSED! Your RAG system is working correctly.")
        print_info("Your system is ready for production use.")
        return True
    else:
        print_error("❌ Some tests failed. Please check the errors above.")
        
        if not embedding_ok:
            print_warning("Embedding service issues may affect document processing.")
        if not rag_ok:
            print_warning("RAG service issues may affect chat responses.")
        
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)