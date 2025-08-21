import requests
import json
import os
from dotenv import load_dotenv
import boto3
from qdrant_client import QdrantClient

load_dotenv()

def debug_rag_system():
    print("🔍 RAG System Debugging Script")
    print("=" * 50)
    
    # Test 1: Check Qdrant Connection
    print("\n1. Testing Qdrant Connection...")
    try:
        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.environ.get("QDRANT_API_KEY", "")
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        print(f"✅ Connected to Qdrant at {qdrant_url}")
        print(f"📊 Found {len(collection_names)} collections: {collection_names}")
        
        # Check specific bot collection
        test_bot_id = "40fffdbb-932b-4a2f-aa22-9b004cee27fa"  # From your test file
        if test_bot_id in collection_names:
            collection_info = client.get_collection(test_bot_id)
            print(f"✅ Bot collection '{test_bot_id}' exists")
            print(f"📈 Vector count: {collection_info.points_count}")
            print(f"📏 Vector size: {collection_info.config.params.vectors.size}")
            
            # Get sample points
            sample_points = client.scroll(collection_name=test_bot_id, limit=3)
            print(f"📝 Sample points: {len(sample_points[0])}")
            for i, point in enumerate(sample_points[0][:2]):
                chunk_preview = point.payload.get('chunk', '')[:100] + '...'
                print(f"   Point {i+1}: {chunk_preview}")
        else:
            print(f"❌ Bot collection '{test_bot_id}' does not exist")
            print("💡 This is likely why you're getting no results!")
            
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        return False
    
    # Test 2: Check Bedrock Embedding
    print("\n2. Testing Bedrock Embedding...")
    try:
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime', 
            region_name=os.environ.get("AWS_REGION")
        )
        
        test_query = "What services does logiquad offer?"
        response = bedrock_runtime.invoke_model(
            body=json.dumps({"inputText": test_query}),
            modelId="amazon.titan-embed-text-v2:0",
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())
        query_embedding = response_body.get("embedding")
        
        print(f"✅ Bedrock embedding successful")
        print(f"📏 Embedding type: {type(query_embedding)}")
        print(f"📏 Embedding length: {len(query_embedding) if query_embedding else 'None'}")
        print(f"📊 First 5 values: {query_embedding[:5] if query_embedding else 'None'}")
        
        # Test the .tolist() call
        if hasattr(query_embedding, 'tolist'):
            print("✅ query_embedding has .tolist() method")
        else:
            print("❌ query_embedding does NOT have .tolist() method")
            print("💡 This is the source of your error! Remove .tolist() call")
            
    except Exception as e:
        print(f"❌ Bedrock embedding failed: {e}")
        return False
    
    # Test 3: Test RAG Service Directly
    print("\n3. Testing RAG Service...")
    try:
        url = "http://localhost:8004/chat"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('RAG_SERVICE_KEY', 'your-rag-secret-key')}"
        }
        data = {
            "query": "What services does logiquad offer?",
            "bot_id": "40fffdbb-932b-4a2f-aa22-9b004cee27fa",
            "conversation_id": "debug-test-123"
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"📡 RAG Service Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ RAG Service responded successfully")
            print(f"📝 Answer length: {len(result.get('answer', ''))} characters")
            print(f"📚 Sources found: {len(result.get('sources', []))}")
            print(f"🔍 Answer preview: {result.get('answer', '')[:200]}...")
            
            if len(result.get('sources', [])) == 0:
                print("❌ No sources found - this confirms the Qdrant search issue")
        else:
            print(f"❌ RAG Service error: {response.text}")
            
    except Exception as e:
        print(f"❌ RAG Service test failed: {e}")
    
    # Test 4: Check Environment Variables
    print("\n4. Checking Environment Variables...")
    required_vars = [
        "QDRANT_URL", "QDRANT_API_KEY", "AWS_REGION", 
        "RAG_SERVICE_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"
    ]
    
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 10)}... (set)")
        else:
            print(f"❌ {var}: Not set")
    
    print("\n" + "=" * 50)
    print("🎯 RECOMMENDATIONS:")
    print("1. Check if your bot has any embedded documents in Qdrant")
    print("2. Fix the .tolist() error in rag_service.py if embedding is already a list")
    print("3. Ensure documents are properly crawled and embedded before testing")
    print("4. Verify all environment variables are correctly set")

if __name__ == "__main__":
    debug_rag_system()