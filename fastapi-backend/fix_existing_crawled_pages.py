#!/usr/bin/env python3
"""
Fix existing crawled pages that failed embedding processing
"""

import asyncio
import json
from config.database import init_database_pool, get_db_connection, get_qdrant_client, get_bedrock_client
from utils.helpers import chunk_text, generate_uuid, current_timestamp

async def fix_failed_crawled_pages():
    """Find and fix crawled pages that failed embedding processing"""
    
    print("🔧 Fixing failed crawled pages...")
    
    # Initialize database clients
    await init_database_pool()
    
    try:
        async with get_db_connection() as conn:
            # Find pages with failed status
            failed_pages = await conn.fetch("""
                SELECT id, bot_id, user_id, content, url, title, error
                FROM crawled_pages
                WHERE status = 'failed'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            print(f"📄 Found {len(failed_pages)} failed pages to fix")
            
            for page in failed_pages:
                page_id = page['id']
                bot_id = page['bot_id']
                user_id = page['user_id']
                content = page['content']
                url = page['url']
                
                print(f"\n🔧 Processing page: {url}")
                print(f"   Error was: {page['error'][:100]}...")
                
                try:
                    # Process embeddings for this page
                    await process_page_embeddings(conn, page_id, bot_id, user_id, content)
                    
                    # Update page status to completed
                    await conn.execute("""
                        UPDATE crawled_pages 
                        SET status = 'completed', updated_at = $1, embedded_at = $2, error = NULL
                        WHERE id = $3
                    """, current_timestamp(), current_timestamp(), page_id)
                    
                    print(f"✅ Successfully processed page: {page_id}")
                    
                except Exception as e:
                    print(f"❌ Failed to process page {page_id}: {e}")
                    
                    # Update with new error
                    await conn.execute("""
                        UPDATE crawled_pages 
                        SET status = 'failed', updated_at = $1, error = $2
                        WHERE id = $3
                    """, current_timestamp(), str(e), page_id)
            
            # Check results
            await check_results()
            
    except Exception as e:
        print(f"❌ Error fixing pages: {e}")
        import traceback
        traceback.print_exc()

async def process_page_embeddings(conn, page_id: str, bot_id: str, user_id: str, content: str):
    """Process embeddings for a crawled page"""
    
    # Split content into chunks
    chunks = chunk_text(content)
    print(f"   📝 Split into {len(chunks)} chunks")
    
    if not chunks:
        raise ValueError("No chunks generated")
    
    # Generate embeddings using Bedrock
    embeddings = await generate_embeddings(chunks)
    print(f"   🧠 Generated {len(embeddings)} embeddings")
    
    # Ensure Qdrant collection exists
    await ensure_qdrant_collection(bot_id, len(embeddings[0]) if embeddings else 1024)
    
    # Prepare points for Qdrant
    points = []
    
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_id = generate_uuid()
        qdrant_point_id = generate_uuid()
        
        # Store in database - embedding as array, not JSON string
        await conn.execute("""
            INSERT INTO embedding_chunks (
                id, crawled_page_id, bot_id, user_id, chunk_index,
                chunk_text, chunk_length, embedding_vector, qdrant_point_id,
                created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, 
            chunk_id,
            page_id,
            bot_id,
            user_id,
            i,
            chunk,
            len(chunk),
            embedding,  # Store as array, not JSON string
            qdrant_point_id,
            current_timestamp()
        )
        
        # Prepare Qdrant point
        points.append({
            "id": qdrant_point_id,
            "vector": embedding,
            "payload": {
                "page_id": page_id,
                "chunk_index": i,
                "chunk": chunk,
                "source_type": "crawled_page"
            }
        })
    
    # Upsert points to Qdrant
    qdrant_client = get_qdrant_client()
    qdrant_client.upsert(
        collection_name=bot_id,
        points=points
    )
    
    print(f"   ✅ Stored {len(points)} embeddings in Qdrant")

async def generate_embeddings(chunks):
    """Generate embeddings for text chunks using Bedrock"""
    
    bedrock_client = get_bedrock_client()
    embeddings = []
    
    for chunk in chunks:
        response = bedrock_client.invoke_model(
            body=json.dumps({"inputText": chunk}),
            modelId="amazon.titan-embed-text-v2:0",
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())
        embedding = response_body.get("embedding")
        
        if not embedding:
            raise ValueError(f"No embedding in response: {response_body}")
        
        embeddings.append(embedding)
    
    return embeddings

async def ensure_qdrant_collection(collection_name: str, vector_size: int):
    """Ensure Qdrant collection exists"""
    
    qdrant_client = get_qdrant_client()
    
    try:
        # Check if collection exists
        collections = qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if collection_name not in collection_names:
            # Create collection
            from qdrant_client.models import Distance, VectorParams
            
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            
            print(f"   🗂️  Created Qdrant collection: {collection_name}")
        else:
            print(f"   ✅ Qdrant collection already exists: {collection_name}")
            
    except Exception as e:
        # If collection already exists, that's fine
        if "already exists" in str(e):
            print(f"   ✅ Qdrant collection already exists: {collection_name}")
        else:
            raise

async def check_results():
    """Check the results of the fix"""
    
    print(f"\n📊 Checking results...")
    
    async with get_db_connection() as conn:
        # Count pages by status
        status_counts = await conn.fetch("""
            SELECT status, COUNT(*) as count
            FROM crawled_pages
            GROUP BY status
            ORDER BY count DESC
        """)
        
        print(f"📄 Crawled pages by status:")
        for row in status_counts:
            print(f"   {row['status']}: {row['count']}")
        
        # Count embedding chunks
        chunk_count = await conn.fetchval("""
            SELECT COUNT(*) FROM embedding_chunks
        """)
        print(f"🧠 Total embedding chunks: {chunk_count}")
        
        # Check Qdrant collections
        try:
            qdrant_client = get_qdrant_client()
            collections = qdrant_client.get_collections()
            
            print(f"🗂️  Qdrant collections:")
            for collection in collections.collections:
                collection_info = qdrant_client.get_collection(collection.name)
                print(f"   {collection.name}: {collection_info.points_count} points")
                
        except Exception as e:
            print(f"❌ Error checking Qdrant: {e}")

if __name__ == "__main__":
    print("🚀 Starting crawled pages fix...\n")
    
    asyncio.run(fix_failed_crawled_pages())
    
    print(f"\n🎉 Fix completed!")
    print(f"💡 Failed pages should now be properly embedded in Qdrant")