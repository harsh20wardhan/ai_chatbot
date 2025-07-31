# Realtime Crawling API

This document describes the realtime crawling functionality that allows you to crawl websites, see the crawled text in real-time, embed it, and store it in the vector database for RAG (Retrieval-Augmented Generation).

## Overview

The realtime crawling system consists of:

1. **Realtime Crawl Service** (`realtime_crawl_service.py`) - Handles crawling with real-time updates via WebSocket
2. **API Endpoints** (`api/src/handlers/realtime_crawl.js`) - REST API for managing realtime crawls
3. **Database Schema** - New tables for storing crawled content and embeddings
4. **Test Interface** (`realtime_crawl_test.html`) - Web interface for testing the functionality

## Features

- **Real-time crawling**: See pages being crawled as they happen
- **Live embedding**: Watch as text is chunked and embedded in real-time
- **WebSocket updates**: Real-time progress updates via WebSocket
- **Vector storage**: Automatically stores embeddings in Qdrant vector database
- **Database persistence**: Stores crawled content and metadata in PostgreSQL
- **RAG integration**: Crawled content can be used for question-answering

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Client    │    │  Realtime Crawl  │    │   Vector DB     │
│                 │◄──►│     Service      │───►│   (Qdrant)      │
│  (WebSocket)    │    │   (Port 8005)    │    │  (Port 6333)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   PostgreSQL     │
                       │   (Supabase)     │
                       └──────────────────┘
```

## Database Schema

### New Tables

#### `crawled_pages`
Stores individual pages that have been crawled:
- `id` - Unique identifier
- `crawl_job_id` - Reference to the crawl job
- `bot_id` - Reference to the bot
- `user_id` - Reference to the user
- `url` - The crawled URL
- `title` - Page title
- `content` - Extracted text content
- `content_length` - Length of content
- `status` - pending/embedded/failed
- `created_at` - Timestamp

#### `embedding_chunks`
Stores text chunks and their embeddings:
- `id` - Unique identifier
- `crawled_page_id` - Reference to crawled page
- `bot_id` - Reference to the bot
- `chunk_index` - Position in the page
- `chunk_text` - The text chunk
- `chunk_length` - Length of chunk
- `embedding_vector` - The embedding vector
- `qdrant_point_id` - Reference to Qdrant point

#### `realtime_crawl_sessions`
Manages WebSocket sessions:
- `id` - Unique identifier
- `crawl_job_id` - Reference to crawl job
- `session_token` - WebSocket session token
- `status` - active/closed/expired

## API Endpoints

### Start Realtime Crawl
```
POST /api/realtime-crawl/start
```

**Request Body:**
```json
{
  "url": "https://example.com",
  "maxDepth": 3,
  "botId": "bot-uuid",
  "excludePatterns": ["admin", "login"]
}
```

**Response:**
```json
{
  "message": "Realtime crawl job started successfully",
  "job_id": "job-uuid",
  "session_id": "session-uuid",
  "websocket_url": "ws://localhost:8005"
}
```

### Get Crawl Status
```
GET /api/realtime-crawl/status/:jobId
```

### Get Crawled Pages
```
GET /api/realtime-crawl/pages/:jobId?page=1&limit=20
```

### Get Page Content
```
GET /api/realtime-crawl/page/:pageId/content
```

### Delete Crawled Page
```
DELETE /api/realtime-crawl/page/:pageId
```

## WebSocket Events

### Client to Server
- `join` - Join a crawl session
- `disconnect` - Disconnect from session

### Server to Client
- `connected` - Confirmation of session join
- `crawl_status` - Current crawling status
- `page_crawled` - New page crawled
- `embedding_started` - Embedding process started
- `embedding_progress` - Embedding progress updates
- `embedding_completed` - Embedding completed
- `crawl_completed` - Crawl job completed
- `crawl_error` - Crawl error occurred
- `embedding_error` - Embedding error occurred

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Add these to your `.env` file:

```env
# Realtime Crawl Service
REALTIME_CRAWL_SERVICE_KEY=your-realtime-crawl-secret-key
REALTIME_CRAWL_SECRET_KEY=your-flask-secret-key

# Database
SUPABASE_DB_HOST=your-db-host
SUPABASE_DB_NAME=your-db-name
SUPABASE_DB_USER=your-db-user
SUPABASE_DB_PASSWORD=your-db-password
SUPABASE_DB_PORT=5432

# Vector DB
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key

# Other Services
CRAWLER_SERVICE_URL=http://localhost:8001
CRAWLER_SERVICE_KEY=your-crawler-secret-key
EMBEDDING_SERVICE_URL=http://localhost:8003
EMBEDDING_SERVICE_KEY=your-embedding-secret-key
```

### 3. Start Services

```bash
# Windows
.\start_services_with_realtime.ps1

# Linux/Mac
./start_services_with_realtime.sh
```

### 4. Run Database Migrations

Execute the updated schema in `supabase_schema.sql` to create the new tables.

## Usage Examples

### 1. Using the Test Interface

1. Open `realtime_crawl_test.html` in your browser
2. Enter a website URL (e.g., `https://example.com`)
3. Enter a bot ID (create one via the API first)
4. Click "Start Realtime Crawl"
5. Watch the real-time progress in the log

### 2. Using the API Directly

```javascript
// Start a realtime crawl
const response = await fetch('/api/realtime-crawl/start', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-auth-token'
  },
  body: JSON.stringify({
    url: 'https://example.com',
    maxDepth: 3,
    botId: 'your-bot-id',
    excludePatterns: ['admin', 'login']
  })
});

const data = await response.json();
console.log('Session ID:', data.session_id);

// Connect to WebSocket
const socket = io('ws://localhost:8005');
socket.emit('join', { session_id: data.session_id });

socket.on('page_crawled', (data) => {
  console.log('Page crawled:', data.title);
});

socket.on('embedding_completed', (data) => {
  console.log('Embedding completed:', data.page_id);
});
```

### 3. Using with RAG

After crawling, the content is automatically available for RAG:

```javascript
// Ask questions about the crawled content
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: "What is this website about?",
    bot_id: "your-bot-id",
    conversation_id: "conversation-uuid"
  })
});
```

## Configuration

### Crawling Settings

- **Max Depth**: How many pages to crawl (default: 3)
- **Exclude Patterns**: URLs containing these patterns will be skipped
- **Content Filtering**: Automatically removes navigation, footer, ads
- **Minimum Content**: Pages with less than 50 characters are skipped

### Embedding Settings

- **Chunk Size**: 500 characters per chunk (default)
- **Overlap**: 50 characters overlap between chunks
- **Model**: `hkunlp/instructor-xl` (default)
- **Vector Size**: 768 dimensions

### WebSocket Settings

- **Port**: 8005 (default)
- **CORS**: Enabled for all origins
- **Session Timeout**: 24 hours
- **Max Connections**: No limit

## Monitoring and Logs

### Log Files

- `logs/realtime_crawl.log` - Realtime crawl service logs
- `logs/crawler.log` - Original crawler service logs
- `logs/embedding.log` - Embedding service logs

### Database Queries

```sql
-- Check crawl jobs
SELECT * FROM crawl_jobs WHERE bot_id = 'your-bot-id';

-- Check crawled pages
SELECT * FROM crawled_pages WHERE crawl_job_id = 'job-id';

-- Check embedding chunks
SELECT * FROM embedding_chunks WHERE crawled_page_id = 'page-id';

-- Get crawl statistics
SELECT 
  COUNT(*) as total_pages,
  COUNT(CASE WHEN status = 'embedded' THEN 1 END) as embedded_pages,
  COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_pages
FROM crawled_pages 
WHERE crawl_job_id = 'job-id';
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check if the realtime crawl service is running on port 8005
   - Verify firewall settings
   - Check browser console for errors

2. **Database Connection Error**
   - Verify database credentials in `.env`
   - Check if Supabase is accessible
   - Ensure database schema is up to date

3. **Embedding Model Loading**
   - First run may take time to download the model
   - Check internet connection
   - Verify sufficient disk space

4. **Qdrant Connection Error**
   - Ensure Qdrant is running on port 6333
   - Check Qdrant API key
   - Verify collection creation permissions

### Performance Tips

1. **Limit Crawl Depth**: Start with depth 2-3 for testing
2. **Use Exclude Patterns**: Skip irrelevant pages
3. **Monitor Memory**: Large sites may require more RAM
4. **Batch Processing**: Consider crawling in smaller batches

## Security Considerations

1. **Authentication**: All API endpoints require authentication
2. **Rate Limiting**: Implement rate limiting for production
3. **Input Validation**: URLs are validated before crawling
4. **Content Filtering**: Sensitive content should be excluded
5. **Session Management**: WebSocket sessions have timeouts

## Future Enhancements

1. **Resume Capability**: Resume interrupted crawls
2. **Scheduled Crawling**: Automatically crawl sites on schedule
3. **Content Deduplication**: Remove duplicate content
4. **Advanced Filtering**: More sophisticated content filtering
5. **Analytics Dashboard**: Web interface for monitoring crawls
6. **Export Functionality**: Export crawled data in various formats 