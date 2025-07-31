# AI Chatbot API

This is the API layer for the AI-powered customer support chatbot, implemented as a Cloudflare Worker.

## Features

- Authentication using Supabase
- Bot management
- Website crawling
- Document parsing
- Embedding generation
- Vector database management
- RAG-powered chat functionality
- Admin dashboard metrics

## Setup

### Prerequisites

- Node.js 18+
- Cloudflare account
- Supabase account
- Qdrant (vector database)

### Local Development

1. Install dependencies:
   ```
   npm install
   ```

2. Configure environment variables in `wrangler.toml` or create a `.dev.vars` file for local development:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_supabase_service_key
   QDRANT_URL=your_qdrant_url
   QDRANT_API_KEY=your_qdrant_api_key
   CRAWLER_SERVICE_URL=your_crawler_service_url
   CRAWLER_SERVICE_KEY=your_crawler_service_key
   PARSER_SERVICE_URL=your_parser_service_url
   PARSER_SERVICE_KEY=your_parser_service_key
   EMBEDDINGS_SERVICE_URL=your_embeddings_service_url
   EMBEDDINGS_SERVICE_KEY=your_embeddings_service_key
   RAG_SERVICE_URL=your_rag_service_url
   RAG_SERVICE_KEY=your_rag_service_key
   ```

3. Start development server:
   ```
   npm run dev
   ```

### Deployment

1. Deploy to Cloudflare Workers:
   ```
   npm run deploy
   ```

2. Set up your secret environment variables:
   ```
   npx wrangler secret put SUPABASE_SERVICE_KEY
   npx wrangler secret put QDRANT_API_KEY
   npx wrangler secret put CRAWLER_SERVICE_KEY
   npx wrangler secret put PARSER_SERVICE_KEY
   npx wrangler secret put EMBEDDINGS_SERVICE_KEY
   npx wrangler secret put RAG_SERVICE_KEY
   ```

## Architecture

The API is built as a Cloudflare Worker and acts as the central hub for the entire system. It delegates intensive tasks (crawling, parsing, embedding, and RAG inference) to separate microservices that have access to the necessary compute resources for these operations.

### Microservices Integration

- **Crawler Service**: Python service that crawls websites and extracts content
- **Parser Service**: Python service that parses documents (PDF, DOCX, etc.)
- **Embeddings Service**: Python service that generates text embeddings using InstructorXL
- **RAG Service**: Python service that handles the RAG pipeline with LLM integration

## API Routes

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Log in
- `POST /api/auth/logout` - Log out
- `GET /api/auth/user` - Get current user

### Bot Management
- `GET /api/bots` - Get all bots
- `POST /api/bots` - Create a new bot
- `GET /api/bots/:botId` - Get a specific bot
- `PUT /api/bots/:botId` - Update a bot
- `DELETE /api/bots/:botId` - Delete a bot

### Crawler
- `POST /api/crawl/website` - Start a website crawl
- `GET /api/crawl/status/:jobId` - Get crawl job status
- `DELETE /api/crawl/job/:jobId` - Cancel a crawl job

### Document Parser
- `POST /api/documents/upload` - Upload and parse a document
- `GET /api/documents` - List all documents
- `GET /api/documents/:documentId` - Get a specific document
- `DELETE /api/documents/:documentId` - Delete a document

### Embeddings
- `POST /api/embeddings/generate` - Generate embeddings for documents
- `GET /api/embeddings/status/:jobId` - Get embedding job status
- `DELETE /api/embeddings/delete/:botId` - Delete embeddings for a bot

### Vector DB
- `GET /api/vectors/collections` - List collections
- `POST /api/vectors/collections` - Create a collection
- `DELETE /api/vectors/collections/:collectionId` - Delete a collection

### Chat
- `POST /api/chat` - Process a chat message using RAG
- `GET /api/chat/conversations` - List conversations
- `GET /api/chat/conversations/:conversationId` - Get a conversation

### Admin
- `GET /api/admin/stats` - Get admin statistics
- `GET /api/admin/logs` - Get system logs
- `GET /api/admin/jobs` - Get active jobs

### Widget
- `GET /api/widget/:botId/config` - Get widget configuration
- `POST /api/widget/:botId/config` - Update widget configuration 