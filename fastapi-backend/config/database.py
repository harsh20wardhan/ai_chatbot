"""
Database Connection Management

Handles PostgreSQL connections to Supabase database with connection pooling
and shared client initialization for external services.
"""

import asyncio
import logging
from typing import Optional
import asyncpg
import boto3
from qdrant_client import QdrantClient
from supabase import create_client, Client

from .settings import settings

logger = logging.getLogger(__name__)

# Global connection pool and clients
_db_pool: Optional[asyncpg.Pool] = None
_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None
_qdrant_client: Optional[QdrantClient] = None
_bedrock_client = None

async def init_db():
    """Initialize database connection pool and external service clients"""
    global _db_pool, _supabase_client, _supabase_admin_client, _qdrant_client, _bedrock_client
    
    # Initialize Supabase clients first (these are more likely to work)
    try:
        logger.info("Initializing Supabase clients...")
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        _supabase_admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase clients initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase clients: {e}", exc_info=True)
        # Don't raise here, continue with other services
    
    # Initialize PostgreSQL connection pool with retry logic
    try:
        logger.info("Initializing database connection pool...")
        # Try with SSL first (Supabase requires SSL)
        _db_pool = await asyncpg.create_pool(
            host=settings.SUPABASE_DB_HOST,
            port=settings.SUPABASE_DB_PORT,
            user=settings.SUPABASE_DB_USER,
            password=settings.SUPABASE_DB_PASSWORD,
            database=settings.SUPABASE_DB_NAME,
            min_size=1,  # Reduced from 5 to 1 for initial connection
            max_size=10,  # Reduced from 20 to 10
            command_timeout=30,  # Reduced from 60 to 30
            ssl='require',  # Supabase requires SSL
            statement_cache_size=0,  # Disable prepared statements for pgbouncer compatibility
            server_settings={
                'jit': 'off'  # Disable JIT for better connection stability
            }
        )
        logger.info("Database connection pool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database connection pool: {e}")
        logger.warning("Will use Supabase REST API instead of direct database connection.")
        # Don't raise here, allow the app to start without direct DB connection
    
    # Initialize Qdrant client
    try:
        logger.info("Initializing Qdrant client...")
        _qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        # Test Qdrant connection with timeout
        collections = _qdrant_client.get_collections()
        logger.info(f"Qdrant client initialized successfully. Found {len(collections.collections)} collections")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant client: {e}")
        logger.warning("Application will start without Qdrant connection. Vector search features may not work.")
        # Don't raise here, continue
    
    # Initialize Bedrock client
    try:
        logger.info("Initializing AWS Bedrock client...")
        _bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        logger.info("AWS Bedrock client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AWS Bedrock client: {e}")
        logger.warning("Application will start without Bedrock connection. AI features may not work.")
        # Don't raise here, continue

async def close_db():
    """Close database connection pool and cleanup clients"""
    global _db_pool, _supabase_client, _supabase_admin_client, _qdrant_client, _bedrock_client
    
    try:
        if _db_pool:
            logger.info("Closing database connection pool...")
            await _db_pool.close()
            _db_pool = None
            logger.info("Database connection pool closed")
        
        # Cleanup clients
        _supabase_client = None
        _supabase_admin_client = None
        _qdrant_client = None
        _bedrock_client = None
        
        logger.info("All database connections and clients cleaned up")
        
    except Exception as e:
        logger.error(f"Error closing database connections: {e}", exc_info=True)

# Aliases for the new naming convention
async def init_database_pool():
    """Alias for init_db() - Initialize database connection pool and external service clients"""
    await init_db()

async def close_database_pool():
    """Alias for close_db() - Close database connection pool and cleanup clients"""
    await close_db()

def get_db_pool() -> Optional[asyncpg.Pool]:
    """Get the database connection pool"""
    if _db_pool is None:
        logger.warning("Database pool not initialized. Some features may not work.")
    return _db_pool

def get_supabase_client() -> Optional[Client]:
    """Get the Supabase client (anon key)"""
    if _supabase_client is None:
        logger.warning("Supabase client not initialized. Some features may not work.")
    return _supabase_client

def get_supabase_admin_client() -> Optional[Client]:
    """Get the Supabase admin client (service role key)"""
    if _supabase_admin_client is None:
        logger.warning("Supabase admin client not initialized. Some features may not work.")
    return _supabase_admin_client

def get_qdrant_client() -> Optional[QdrantClient]:
    """Get the Qdrant client"""
    if _qdrant_client is None:
        logger.warning("Qdrant client not initialized. Vector search features may not work.")
    return _qdrant_client

def get_bedrock_client():
    """Get the AWS Bedrock client"""
    if _bedrock_client is None:
        logger.warning("Bedrock client not initialized. AI features may not work.")
    return _bedrock_client

# Database connection context manager for transactions
class DatabaseConnection:
    """Context manager for database connections with transaction support"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.connection: Optional[asyncpg.Connection] = None
        self.transaction: Optional[asyncpg.Transaction] = None
    
    async def __aenter__(self) -> asyncpg.Connection:
        self.connection = await self.pool.acquire()
        return self.connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            await self.pool.release(self.connection)

class DatabaseTransaction:
    """Context manager for database transactions"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.connection: Optional[asyncpg.Connection] = None
        self.transaction: Optional[asyncpg.Transaction] = None
    
    async def __aenter__(self) -> asyncpg.Connection:
        self.connection = await self.pool.acquire()
        self.transaction = self.connection.transaction()
        await self.transaction.start()
        return self.connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.transaction:
            if exc_type is None:
                await self.transaction.commit()
            else:
                await self.transaction.rollback()
        
        if self.connection:
            await self.pool.release(self.connection)

def get_db_connection() -> DatabaseConnection:
    """Get a database connection context manager"""
    pool = get_db_pool()
    if pool is None:
        raise RuntimeError("Database pool not available. Check database connection.")
    return DatabaseConnection(pool)

def get_db_transaction() -> DatabaseTransaction:
    """Get a database transaction context manager"""
    pool = get_db_pool()
    if pool is None:
        raise RuntimeError("Database pool not available. Check database connection.")
    return DatabaseTransaction(pool)