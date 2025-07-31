# AI Chatbot with RAG

Open-source AI customer support chatbot using retrieval-augmented generation (RAG) built with free and open-source tools.

## Architecture

The system consists of the following components:

1. **Cloudflare Worker API** - Central API gateway for all client interactions
2. **Crawler Service** - Python microservice for website crawling
3. **Parser Service** - Python microservice for document parsing
4. **Embedding Service** - Python microservice for text embedding
5. **RAG Service** - Python microservice for the RAG pipeline
6. **Vector DB** - Qdrant for storing and retrieving embeddings
7. **Supabase** - Authentication, database, and storage
8. **Ollama** - Local LLM for generating responses

## Quick Start Guide

### 1. Prerequisites Installation

#### Install Python 3.12+
```bash
# Windows: Download from python.org
# Linux/macOS: Use package manager or pyenv
```

#### Install Node.js 18+
```bash
# Windows: Download from nodejs.org
# Linux/macOS: Use package manager or nvm
```

#### Install Docker Desktop
```bash
# Download from docker.com
# Ensure Docker is running
```

#### Install Ollama
```bash
# Download from ollama.ai
# Start Ollama: ollama serve
```

### 2. Project Setup

#### Clone and Navigate
```bash
git clone <your-repo-url>
cd ai_chatbot
```

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Install Node.js Dependencies
```bash
cd api
npm install
cd ..
```

### 3. Environment Configuration

#### Create `.env` file in root directory
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key
CRAWLER_SERVICE_KEY=your-crawler-secret-key
PARSER_SERVICE_KEY=your-parser-secret-key
EMBEDDINGS_SERVICE_KEY=your-embedding-secret-key
RAG_SERVICE_KEY=your-rag-secret-key
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=mistral:7b
ALLOWED_ORIGIN=*
```

#### Create `.dev.vars` file in `api` directory
```bash
# Copy the same variables from .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key
CRAWLER_SERVICE_KEY=your-crawler-secret-key
PARSER_SERVICE_KEY=your-parser-secret-key
EMBEDDINGS_SERVICE_KEY=your-embedding-secret-key
RAG_SERVICE_KEY=your-rag-secret-key
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=mistral:7b
ALLOWED_ORIGIN=*
```

### 4. Database Setup

#### Start Qdrant Vector Database
```bash
cd vector_db
docker-compose up -d
cd ..
```

#### Setup Supabase Database
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the SQL from `supabase_schema.sql`

### 5. Install Ollama Models

#### Install Fast Model (Recommended)
```bash
ollama pull mistral:7b
```

#### Alternative Fast Models
```bash
# For ultra-fast responses
ollama pull phi3:mini

# For balanced speed/quality
ollama pull llama2:7b

# For best quality (slower)
ollama pull deepseek-r1:8b
```

### 6. Start All Services

#### Option 1: Using Startup Script (Recommended)
```bash
# Linux/macOS
./start_services.sh

# Windows
start_services.bat
```

#### Option 2: Manual Startup
```bash
# Terminal 1: Start Qdrant (if not already running)
cd vector_db && docker-compose up -d

# Terminal 2: Start RAG Service
python rag_service.py

# Terminal 3: Start API Service
cd api && npm run dev

# Terminal 4: Start other services (optional)
python crawler_service.py
python parser_service.py
python embedding_service.py
```

### 7. Verify Installation

#### Check Services
```bash
# Check if services are running
curl http://localhost:8004/chat  # RAG Service
curl http://localhost:8787/api/health  # API Service
curl http://localhost:6333/collections  # Qdrant
```

#### Test Chat API
```bash
# Create a test bot first via Supabase dashboard
# Then test the chat API
curl -X POST http://localhost:8787/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "bot_id": "your-bot-id",
    "query": "Hello, how are you?",
    "conversation_id": "test-conv-123"
  }'
```

## Service Ports

- **API Gateway**: http://localhost:8787
- **RAG Service**: http://localhost:8004
- **Crawler Service**: http://localhost:8001
- **Parser Service**: http://localhost:8002
- **Embedding Service**: http://localhost:8003
- **Qdrant**: http://localhost:6333
- **Ollama**: http://localhost:11434

## Troubleshooting

### Common Issues

#### 1. Python Dependencies
```bash
# If you get import errors, upgrade packages
pip install --upgrade sentence-transformers torch PyPDF2
```

#### 2. Ollama Connection Issues
```bash
# Ensure Ollama is running
ollama serve

# Check available models
ollama list

# Test Ollama directly
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:7b", "prompt": "Hello", "stream": false}'
```

#### 3. RAG Service Timeout
- Increase timeout in `rag_service.py` (already set to 60 seconds)
- Use faster models like `mistral:7b` or `phi3:mini`

#### 4. Database Connection Issues
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Restart Qdrant if needed
cd vector_db && docker-compose restart
```

#### 5. API Authentication Issues
- Ensure Supabase JWT token is valid
- Check `.env` and `.dev.vars` files have correct keys
- Verify database schema is properly set up

### Performance Optimization

#### For Faster Responses
1. Use smaller models: `mistral:7b`, `phi3:mini`, `llama2:7b`
2. Ensure adequate RAM (8GB+ recommended)
3. Use SSD storage for better I/O performance

#### For Better Quality
1. Use larger models: `deepseek-r1:8b`, `llama3:8b`
2. Increase timeout settings
3. Add more context to prompts

## API Documentation

### Chat Endpoint
```bash
POST /api/chat
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>

{
  "bot_id": "uuid",
  "query": "string",
  "conversation_id": "string",
  "message_history": []
}
```

### Bot Management
```bash
# Create Bot
POST /api/bots
Authorization: Bearer <JWT_TOKEN>

# List Bots
GET /api/bots
Authorization: Bearer <JWT_TOKEN>

# Delete Bot
DELETE /api/bots/{bot_id}
Authorization: Bearer <JWT_TOKEN>
```

## Development

### Adding Documents to Bots
1. Upload documents via the API
2. Documents are parsed and embedded
3. Embeddings are stored in Qdrant
4. RAG service retrieves relevant context

### Customizing Models
- Change `OLLAMA_MODEL` in `.env` and `.dev.vars`
- Pull new models: `ollama pull <model-name>`
- Restart RAG service after changes

### Logs
- API logs: `logs/api.log`
- RAG logs: `logs/rag.log`
- Crawler logs: `logs/crawler.log`
- Parser logs: `logs/parser.log`
- Embedding logs: `logs/embedding.log`

## License

MIT 