#!/usr/bin/env python3
"""
Simple database connection test to diagnose Supabase connection issues
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_connection():
    """Test direct connection to Supabase database"""
    
    # Get connection details from environment
    host = os.getenv('SUPABASE_DB_HOST', 'db.qpfljbjbyuiymeqghvsz.supabase.co')
    port = int(os.getenv('SUPABASE_DB_PORT', '5432'))
    user = os.getenv('SUPABASE_DB_USER', 'postgres')
    password = os.getenv('SUPABASE_DB_PASSWORD', 'Nick4dawin99@')
    database = os.getenv('SUPABASE_DB_NAME', 'postgres')
    
    print(f"Testing connection to:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  User: {user}")
    print(f"  Database: {database}")
    print(f"  Password: {'*' * len(password) if password else 'None'}")
    print()
    
    try:
        print("Attempting to connect...")
        
        # Try direct connection first
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            ssl='require'  # Supabase requires SSL
        )
        
        print("✅ Connection successful!")
        
        # Test a simple query
        result = await conn.fetchval("SELECT version()")
        print(f"✅ Query test successful: {result[:50]}...")
        
        await conn.close()
        print("✅ Connection closed successfully")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Try without SSL
        try:
            print("\nTrying without SSL requirement...")
            conn = await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            print("✅ Connection without SSL successful!")
            await conn.close()
        except Exception as e2:
            print(f"❌ Connection without SSL also failed: {e2}")

if __name__ == "__main__":
    asyncio.run(test_connection())