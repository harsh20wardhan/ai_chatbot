#!/usr/bin/env python3
"""
Test script for the realtime crawl service with pg8000 PostgreSQL adapter
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_realtime_crawl_service():
    print("Testing realtime crawl service...")
    test_data = {
        "url": "https://example.com",
        "max_depth": 2,
        "exclude_patterns": ["admin", "login"],
        "bot_id": "test-bot-123",
        "job_id": "test-job-456"
    }
    try:
        response = requests.post(
            "http://localhost:8005/realtime-crawl",
            json=test_data,
            headers={"Authorization": f"Bearer {os.environ.get('REALTIME_CRAWL_SERVICE_KEY', 'your-realtime-crawl-secret-key')}"},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Realtime crawl service is working!")
            print(f"   Session ID: {result.get('session_id')}")
            print(f"   Status: {result.get('status')}")
            return True
        else:
            print(f"❌ Realtime crawl service failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to realtime crawl service (port 8005)")
        print("   Make sure the service is running")
        return False
    except Exception as e:
        print(f"❌ Error testing realtime crawl service: {e}")
        return False

def test_api_endpoints():
    print("\nTesting API endpoints...")
    test_data = {
        "url": "https://example.com",
        "max_depth": 2,
        "exclude_patterns": ["admin", "login"],
        "bot_id": "test-bot-123"
    }
    try:
        response = requests.post(
            "http://localhost:8787/api/realtime-crawl/start",
            json=test_data,
            headers={"Authorization": f"Bearer {os.environ.get('API_KEY', 'your-api-key')}"},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API start endpoint is working!")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Session ID: {result.get('session_id')}")
            return result.get('job_id')
        else:
            print(f"❌ API start endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API (port 8787)")
        print("   Make sure the Cloudflare Worker is running")
        return None
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return None

def test_database_connection():
    print("\nTesting database connection...")
    try:
        import pg8000
        conn = pg8000.connect(
            host=os.environ.get("SUPABASE_DB_HOST"),
            database=os.environ.get("SUPABASE_DB_NAME"),
            user=os.environ.get("SUPABASE_DB_USER"),
            password=os.environ.get("SUPABASE_DB_PASSWORD"),
            port=int(os.environ.get("SUPABASE_DB_PORT", "5432"))
        )
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version_row = cur.fetchone()
            print(f"✅ Database connection successful!")
            print(f"   PostgreSQL version: {version_row[0]}")
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('crawled_pages', 'embedding_chunks', 'realtime_crawl_sessions')
            """)
            tables = cur.fetchall()
            table_names = [row[0] for row in tables]
            print(f"   Found tables: {table_names}")
            if set(['crawled_pages', 'embedding_chunks', 'realtime_crawl_sessions']).issubset(set(table_names)):
                print("✅ All required tables exist!")
            else:
                print("⚠️  Some tables are missing. Make sure to run the SQL schema.")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_qdrant_connection():
    print("\nTesting Qdrant connection...")
    try:
        from qdrant_client import QdrantClient
        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.environ.get("QDRANT_API_KEY", "")
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        collections = client.get_collections()
        print(f"✅ Qdrant connection successful!")
        print(f"   URL: {qdrant_url}")
        print(f"   Collections: {len(collections.collections)}")
        return True
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        return False

def main():
    print("🧪 Testing Realtime Crawl System")
    print("=" * 50)
    db_ok = test_database_connection()
    qdrant_ok = test_qdrant_connection()
    service_ok = test_realtime_crawl_service()
    job_id = test_api_endpoints()
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Database Connection: {'✅' if db_ok else '❌'}")
    print(f"   Qdrant Connection: {'✅' if qdrant_ok else '❌'}")
    print(f"   Realtime Service: {'✅' if service_ok else '❌'}")
    print(f"   API Endpoints: {'✅' if job_id else '❌'}")
    if all([db_ok, qdrant_ok, service_ok, job_id]):
        print("\n🎉 All tests passed! The realtime crawl system is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        print("\nNext steps:")
        if not db_ok:
            print("   - Check your database connection settings in .env")
            print("   - Make sure the SQL schema has been applied")
        if not qdrant_ok:
            print("   - Start Qdrant: docker-compose up -d (in vector_db directory)")
        if not service_ok:
            print("   - Start the realtime crawl service: python realtime_crawl_service.py")
        if not job_id:
            print("   - Start the Cloudflare Worker API")

if __name__ == "__main__":
    main() 