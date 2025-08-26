"""
Test configuration and fixtures for FastAPI backend tests
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncpg

from main import app
from config.settings import settings
from config.database import init_database_pool, close_database_pool

# Test database URL (should be different from production)
TEST_DATABASE_URL = settings.SUPABASE_DB_HOST.replace("db.", "test-db.") if hasattr(settings, 'SUPABASE_DB_HOST') else "localhost"

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_database():
    """Set up test database and initialize connections"""
    # Initialize database connections for testing
    await init_database_pool()
    yield
    # Clean up
    await close_database_pool()

@pytest.fixture
def client() -> TestClient:
    """Create a test client for synchronous tests"""
    return TestClient(app)

@pytest.fixture
async def async_client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for asynchronous tests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_user():
    """Mock user data for testing"""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "aud": "authenticated",
        "role": "authenticated"
    }

@pytest.fixture
def mock_bot():
    """Mock bot data for testing"""
    return {
        "id": "test-bot-id",
        "name": "Test Bot",
        "description": "A test bot",
        "website_url": "https://example.com",
        "user_id": "test-user-id"
    }

@pytest.fixture
def auth_headers(mock_user):
    """Create authentication headers for testing"""
    # In a real test, you'd create a proper JWT token
    # For now, we'll use a mock token
    return {
        "Authorization": "Bearer mock-jwt-token"
    }

@pytest.fixture
async def test_db_connection():
    """Create a test database connection"""
    try:
        conn = await asyncpg.connect(
            host=settings.SUPABASE_DB_HOST,
            port=settings.SUPABASE_DB_PORT,
            user=settings.SUPABASE_DB_USER,
            password=settings.SUPABASE_DB_PASSWORD,
            database=settings.SUPABASE_DB_NAME
        )
        yield conn
    finally:
        await conn.close()

# Test data cleanup fixtures
@pytest.fixture
async def cleanup_test_data(test_db_connection):
    """Clean up test data after tests"""
    yield
    # Clean up test data
    await test_db_connection.execute("DELETE FROM bots WHERE name LIKE 'Test%'")
    await test_db_connection.execute("DELETE FROM documents WHERE filename LIKE 'test%'")
    await test_db_connection.execute("DELETE FROM crawl_jobs WHERE url LIKE '%test%'")

# Mock external services
@pytest.fixture
def mock_qdrant_client(monkeypatch):
    """Mock Qdrant client for testing"""
    class MockQdrantClient:
        def get_collections(self):
            return type('obj', (object,), {'collections': []})
        
        def create_collection(self, collection_name, vectors_config):
            return True
        
        def delete_collection(self, collection_name):
            return True
        
        def upsert(self, collection_name, points):
            return True
    
    mock_client = MockQdrantClient()
    monkeypatch.setattr("config.database.get_qdrant_client", lambda: mock_client)
    return mock_client

@pytest.fixture
def mock_bedrock_client(monkeypatch):
    """Mock Bedrock client for testing"""
    class MockBedrockClient:
        def invoke_model(self, body, modelId, accept, contentType):
            return {
                "body": type('obj', (object,), {
                    'read': lambda: b'{"embedding": [0.1, 0.2, 0.3]}'
                })
            }
        
        def list_foundation_models(self):
            return {
                "modelSummaries": [
                    {"modelId": "amazon.titan-embed-text-v2:0"}
                ]
            }
    
    mock_client = MockBedrockClient()
    monkeypatch.setattr("config.database.get_bedrock_client", lambda: mock_client)
    return mock_client

@pytest.fixture
def mock_supabase_client(monkeypatch):
    """Mock Supabase client for testing"""
    class MockSupabaseClient:
        def __init__(self):
            self.auth = type('obj', (object,), {
                'get_settings': lambda: {"external": {}}
            })
            self.storage = type('obj', (object,), {
                'list_buckets': lambda: [],
                'from_': lambda bucket: type('obj', (object,), {
                    'download': lambda path: b'test file content'
                })
            })
    
    mock_client = MockSupabaseClient()
    monkeypatch.setattr("config.database.get_supabase_admin_client", lambda: mock_client)
    return mock_client