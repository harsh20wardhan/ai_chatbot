# AI Chatbot Platform

A comprehensive AI chatbot platform with RAG (Retrieval-Augmented Generation) capabilities, dashboard for bot management, and embeddable widget for website integration.

## Overview

This platform allows you to create AI chatbots powered by RAG technology. You can:
- Crawl websites to provide context for your bot
- Upload and parse documents (PDF, DOCX, TXT, Excel)
- Configure and customize the chat widget
- Embed the chatbot on any website
- Track usage and performance analytics

## System Architecture

The platform consists of several components:

1. **API Gateway** (Cloudflare Worker)
   - Handles authentication and routing
   - Communicates with microservices

2. **Microservices**
   - `crawler_service.py`: Extracts content from websites
   - `realtime_crawl_service.py`: Real-time crawling with WebSocket updates
   - `parser_service.py`: Processes documents (PDF, DOCX, TXT, Excel)
   - `embedding_service.py`: Generates vector embeddings
   - `rag_service.py`: Retrieves context and integrates with LLM

3. **Dashboard** (React)
   - Frontend for bot management and configuration
   - Analytics and monitoring

4. **Widget** (React)
   - Embeddable chat interface for websites
   - Customizable appearance and behavior

5. **Databases**
   - PostgreSQL (Supabase) for relational data
   - Qdrant for vector storage

## Prerequisites

- Node.js 18+
- Python 3.9+
- Docker (for Qdrant)
- Supabase account

## Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-chatbot.git
   cd ai-chatbot
   ```

2. Copy the example environment file and edit it with your configuration:
   ```bash
   cp env.example .env
   ```

3. Configure the following environment variables in `.env`:

   ```
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your-service-key
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_DB_HOST=db.your-project.supabase.co
   SUPABASE_DB_NAME=postgres
   SUPABASE_DB_USER=postgres
   SUPABASE_DB_PASSWORD=your-db-password
   SUPABASE_DB_PORT=5432

   # Qdrant Configuration
   QDRANT_URL=http://localhost:6333
   QDRANT_API_KEY=your-qdrant-api-key

   # Service Keys
   CRAWLER_SERVICE_KEY=your-crawler-service-key
   PARSER_SERVICE_KEY=your-parser-service-key
   EMBEDDINGS_SERVICE_KEY=your-embeddings-service-key
   RAG_SERVICE_KEY=your-rag-service-key
   REALTIME_CRAWL_SERVICE_KEY=your-realtime-crawl-service-key

   # Service URLs
   CRAWLER_SERVICE_URL=http://localhost:8001
   PARSER_SERVICE_URL=http://localhost:8002
   EMBEDDINGS_SERVICE_URL=http://localhost:8003
   RAG_SERVICE_URL=http://localhost:8004
   REALTIME_CRAWL_SERVICE_URL=http://localhost:8005

   # Ollama Configuration
   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=llama2
   ```

## Installation

### 1. Set up Qdrant Vector Database

```bash
cd vector_db
docker-compose up -d
```

### 2. Set up Python Services

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Set up API Gateway

```bash
cd api
npm install
```

### 4. Set up Dashboard

```bash
cd dashboard
npm install
```

### 5. Set up Widget

```bash
cd widget
npm install
```

## Starting the Services

### Option 1: Start All Services with Script

Use the provided script to start all services:

```bash
# On Linux/Mac
./start_services.sh

# On Windows PowerShell
.\start_services.ps1
```

This will start:
- Qdrant (if not already running)
- All Python microservices
- API Gateway

### Option 2: Start Services Individually

#### 1. Start Python Microservices

Open separate terminal windows for each service:

```bash
# Crawler Service
python crawler_service.py

# Parser Service
python parser_service.py

# Embedding Service
python embedding_service.py

# RAG Service
python rag_service.py

# Realtime Crawl Service
python realtime_crawl_service.py
```

#### 2. Start API Gateway

```bash
cd api
npm run dev
```

#### 3. Start Dashboard

```bash
cd dashboard
npm start
```

This will start the dashboard on http://localhost:3000

#### 4. Start Widget Development Server (optional, for development only)

```bash
cd widget
npm run dev
```

This will start the widget development server on http://localhost:9000

## Building for Production

### API Gateway

```bash
cd api
npm run build
# Deploy the built worker to Cloudflare
npx wrangler publish
```

### Dashboard

```bash
cd dashboard
npm run build
# The build output will be in the build directory
# Deploy this to your web hosting service
```

### Widget

```bash
cd widget
npm run build
# The build output will be in the dist directory
# Deploy this to your web hosting service or CDN
```

## Using the Platform

1. Access the dashboard at `http://localhost:3000` (or your deployed URL)
2. Log in or register a new account
3. Create a new bot
4. Configure the bot settings and widget appearance
5. Upload documents or crawl websites to provide context
6. Get the embed code for your website

## Embedding the Widget on Your Website

Add the widget to your website by adding the following code before the closing `</body>` tag:

```html
<script>
  (function(w, d, s, o) {
    w.AIChatWidget = o;
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(o)) return;
    js = d.createElement(s); js.id = o;
    js.src = 'https://your-domain.com/widget/ai-chatbot-widget.js';
    js.async = 1;
    js.dataset.botId = 'YOUR_BOT_ID';
    fjs.parentNode.insertBefore(js, fjs);
  }(window, document, 'script', 'ai-chatbot-widget'));
</script>
```

Replace `YOUR_BOT_ID` with the ID of your bot from the dashboard.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Log in
- `POST /api/auth/logout` - Log out
- `GET /api/auth/user` - Get current user

### Bots
- `GET /api/bots` - Get all bots
- `POST /api/bots` - Create a new bot
- `GET /api/bots/:botId` - Get a specific bot
- `PUT /api/bots/:botId` - Update a bot
- `DELETE /api/bots/:botId` - Delete a bot

### Crawling
- `POST /api/crawl/website` - Start a crawl job
- `GET /api/crawl/status/:jobId` - Get crawl status
- `DELETE /api/crawl/job/:jobId` - Delete a crawl job

### Realtime Crawling
- `POST /api/realtime-crawl/start` - Start a realtime crawl job
- `GET /api/realtime-crawl/status/:jobId` - Get realtime crawl status
- `GET /api/realtime-crawl/pages/:jobId` - Get crawled pages
- `GET /api/realtime-crawl/page/:pageId/content` - Get page content
- `DELETE /api/realtime-crawl/page/:pageId` - Delete a crawled page

### Documents
- `POST /api/documents/upload` - Upload a document
- `GET /api/documents` - Get all documents
- `GET /api/documents/:documentId` - Get a specific document
- `DELETE /api/documents/:documentId` - Delete a document

### Widget
- `GET /api/widget/:botId/config` - Get widget configuration
- `POST /api/widget/:botId/config` - Update widget configuration

### Chat
- `POST /api/chat` - Send a message to the bot
- `GET /api/chat/conversations` - Get all conversations
- `GET /api/chat/conversations/:conversationId` - Get a specific conversation

## Troubleshooting

### Database Connection Issues
- Verify your Supabase credentials in the `.env` file
- Check if the database is accessible from your network

### Qdrant Connection Issues
- Ensure Docker is running
- Verify Qdrant is running with `docker ps`
- Check the Qdrant logs with `docker logs vector_db_qdrant_1`

### Python Service Issues
- Check the logs in the `logs` directory
- Verify all required Python packages are installed
- Ensure Python 3.9+ is being used

### API Gateway Issues
- Check the Cloudflare Worker logs
- Verify the environment variables are set correctly

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.