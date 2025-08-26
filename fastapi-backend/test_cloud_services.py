#!/usr/bin/env python3

"""
Cloud Services Test Script

This script tests the connection to Qdrant Cloud and AWS Bedrock
to ensure the configuration is working correctly.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from config.database import get_qdrant_client, get_bedrock_client

async def test_qdrant_cloud():
    """Test Qdrant Cloud connection"""
    print("🔍 Testing Qdrant Cloud connection...")
    print(f"   URL: {settings.QDRANT_URL}")
    print(f"   API Key: {settings.QDRANT_API_KEY[:20]}...")
    
    try:
        # Try to get the initialized client first, otherwise create a new one
        try:
            qdrant_client = get_qdrant_client()
        except RuntimeError:
            from qdrant_client import QdrantClient
            qdrant_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
        
        # Test basic connection
        collections = qdrant_client.get_collections()
        print(f"✅ Qdrant Cloud connected successfully!")
        print(f"   Collections found: {len(collections.collections)}")
        
        # List existing collections
        if collections.collections:
            print("   Existing collections:")
            for collection in collections.collections:
                print(f"     - {collection.name}")
        else:
            print("   No collections found (this is normal for a new setup)")
        
        return True
        
    except Exception as e:
        print(f"❌ Qdrant Cloud connection failed: {e}")
        return False

def test_bedrock_models():
    """Test AWS Bedrock model access"""
    print("\n🔍 Testing AWS Bedrock model access...")
    print(f"   RAG Model: {settings.BEDROCK_RAG_MODEL}")
    print(f"   Embedding Model: {settings.BEDROCK_EMBEDDING_MODEL}")
    print(f"   Region: {settings.AWS_REGION}")
    
    try:
        # Try to get the initialized client first, otherwise create a new one
        try:
            bedrock_client = get_bedrock_client()
        except RuntimeError:
            import boto3
            # Use bedrock client (not bedrock-runtime) for listing models
            bedrock_client = boto3.client(
                'bedrock',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
        
        # List available models
        response = bedrock_client.list_foundation_models()
        models = response.get('modelSummaries', [])
        
        print(f"✅ Bedrock connected successfully!")
        print(f"   Total models available: {len(models)}")
        
        # Check if our specific models are available
        rag_model_available = any(
            model.get('modelId') == settings.BEDROCK_RAG_MODEL 
            for model in models
        )
        embedding_model_available = any(
            model.get('modelId') == settings.BEDROCK_EMBEDDING_MODEL 
            for model in models
        )
        
        print(f"   RAG model ({settings.BEDROCK_RAG_MODEL}): {'✅ Available' if rag_model_available else '❌ Not available'}")
        print(f"   Embedding model ({settings.BEDROCK_EMBEDDING_MODEL}): {'✅ Available' if embedding_model_available else '❌ Not available'}")
        
        if not rag_model_available:
            print("   ⚠️  RAG model not available. Available models:")
            for model in models[:10]:  # Show first 10 models
                print(f"     - {model.get('modelId')}")
        
        return rag_model_available and embedding_model_available
        
    except Exception as e:
        print(f"❌ Bedrock connection failed: {e}")
        return False

def test_bedrock_embedding():
    """Test Bedrock embedding generation"""
    print("\n🔍 Testing Bedrock embedding generation...")
    
    try:
        # Try to get the initialized client first, otherwise create a new one
        try:
            bedrock_client = get_bedrock_client()
        except RuntimeError:
            import boto3
            bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
        
        # Test embedding generation
        test_text = "This is a test sentence for embedding generation."
        
        response = bedrock_client.invoke_model(
            body=json.dumps({"inputText": test_text}),
            modelId=settings.BEDROCK_EMBEDDING_MODEL,
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())
        embedding = response_body.get("embedding")
        
        if embedding and len(embedding) > 0:
            print(f"✅ Embedding generation successful!")
            print(f"   Embedding dimension: {len(embedding)}")
            print(f"   Sample values: {embedding[:5]}...")
            return True
        else:
            print(f"❌ Embedding generation failed: No embedding in response")
            return False
            
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return False

def test_bedrock_rag():
    """Test Bedrock RAG model generation"""
    print("\n🔍 Testing Bedrock RAG model generation...")
    
    try:
        # Try to get the initialized client first, otherwise create a new one
        try:
            bedrock_client = get_bedrock_client()
        except RuntimeError:
            import boto3
            bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
        
        # Test RAG generation with correct OpenAI format
        test_prompt = "Hello, how are you today? Please respond briefly."
        
        request_body = {
            "messages": [
                {"role": "user", "content": test_prompt}
            ],
            "max_completion_tokens": 50,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        response = bedrock_client.invoke_model(
            body=json.dumps(request_body),
            modelId=settings.BEDROCK_RAG_MODEL,
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())
        
        # Try different response formats for OpenAI model
        generated_text = ""
        if "choices" in response_body and len(response_body["choices"]) > 0:
            choice = response_body["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                generated_text = choice["message"]["content"]
        
        if not generated_text:
            generated_text = (
                response_body.get("completion") or 
                response_body.get("text") or 
                response_body.get("generated_text") or
                str(response_body)
            )
        
        if generated_text and len(generated_text.strip()) > 0:
            print(f"✅ RAG model generation successful!")
            print(f"   Response: {generated_text[:100]}...")
            return True
        else:
            print(f"❌ RAG model generation failed: No text in response")
            print(f"   Response body: {response_body}")
            return False
            
    except Exception as e:
        print(f"❌ RAG model generation failed: {e}")
        return False

def test_supabase_connection():
    """Test Supabase database connection"""
    print("\n🔍 Testing Supabase database connection...")
    print(f"   URL: {settings.SUPABASE_URL}")
    print(f"   Host: {settings.SUPABASE_DB_HOST}")
    print(f"   Database: {settings.SUPABASE_DB_NAME}")
    print(f"   User: {settings.SUPABASE_DB_USER}")
    
    try:
        # Try using Supabase client first
        from supabase import create_client
        
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        
        # Test with a simple query
        result = supabase_client.table('information_schema.tables').select('table_name').limit(1).execute()
        
        print(f"✅ Supabase API connected successfully!")
        print(f"   Connection via Supabase client working")
        
        # Try to list tables if possible
        try:
            tables_result = supabase_client.rpc('get_table_names').execute()
            if tables_result.data:
                print(f"   Found tables: {tables_result.data}")
        except:
            print("   ⚠️  Could not list tables (may need custom function or different approach)")
        
        return True
        
    except Exception as supabase_error:
        print(f"❌ Supabase API connection failed: {supabase_error}")
        
        # Try direct PostgreSQL connection as fallback
        try:
            import psycopg2
            
            # Use the correct port for Supabase (5432)
            connection_string = f"postgresql://{settings.SUPABASE_DB_USER}:{settings.SUPABASE_DB_PASSWORD}@{settings.SUPABASE_DB_HOST}:5432/{settings.SUPABASE_DB_NAME}?sslmode=require"
            
            with psycopg2.connect(connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    print(f"✅ Supabase database connected successfully!")
                    print(f"   PostgreSQL version: {version}")
                    
                    # Test if our tables exist
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name IN ('bots', 'documents', 'users');
                    """)
                    tables = cursor.fetchall()
                    
                    if tables:
                        print(f"   Found tables: {[table[0] for table in tables]}")
                    else:
                        print("   ⚠️  No application tables found (may need to run migrations)")
                    
            return True
            
        except Exception as pg_error:
            print(f"❌ Direct PostgreSQL connection also failed: {pg_error}")
            print("   This might be a network connectivity issue")
            return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("Cloud Services Configuration Test")
    print("=" * 60)
    
    # Initialize database and clients
    print("🔧 Initializing database and service clients...")
    try:
        from config.database import init_db
        await init_db()
        print("✅ Database and service clients initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize clients: {e}")
        print("⚠️  Continuing with direct client creation...")
    
    # Test Qdrant Cloud
    qdrant_ok = await test_qdrant_cloud()
    
    # Test Bedrock models
    bedrock_ok = test_bedrock_models()
    
    # Test embedding generation
    embedding_ok = test_bedrock_embedding()
    
    # Test RAG model generation
    rag_ok = test_bedrock_rag()
    
    # Test Supabase connection
    supabase_ok = test_supabase_connection()
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"Qdrant Cloud Connection: {'✅ PASS' if qdrant_ok else '❌ FAIL'}")
    print(f"Bedrock Model Access: {'✅ PASS' if bedrock_ok else '❌ FAIL'}")
    print(f"Embedding Generation: {'✅ PASS' if embedding_ok else '❌ FAIL'}")
    print(f"RAG Model Generation: {'✅ PASS' if rag_ok else '❌ FAIL'}")
    print(f"Supabase Database: {'✅ PASS' if supabase_ok else '❌ FAIL'}")
    
    all_tests_passed = qdrant_ok and bedrock_ok and embedding_ok and rag_ok and supabase_ok
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 All tests passed! Your cloud services are configured correctly.")
        print("\nYou can now start the FastAPI backend with confidence:")
        print("   ./start.sh")
        print("   # or")
        print("   python main.py")
    else:
        print("⚠️  Some tests failed. Please check your configuration:")
        print("\n1. Verify your .env file has the correct credentials")
        print("2. Check your AWS credentials and region")
        print("3. Ensure you have access to the required Bedrock models")
        print("4. Verify your Qdrant Cloud URL and API key")
        print("5. Check your Supabase database connection")
    
    print("=" * 60)
    
    return all_tests_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)