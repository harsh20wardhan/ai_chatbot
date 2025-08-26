# FastAPI Backend

This is the unified FastAPI backend that replaces the Cloudflare Workers API and consolidates all microservices into a single application.

## Features

- **Unified API**: All endpoints in one application
- **Supabase Authentication**: JWT-based authentication using Supabase
- **RAG Chat**: Question-answering using retrieval-augmented generation
- **Document Processing**: PDF, DOCX, TXT, Excel file parsing
- **Web Crawling**: Website crawling with realtime updates
- **Vector Search**: Qdrant integration for semantic search
- **Comprehensive Logging**: Structured logging with correlation IDs

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   Copy the `.env` file and ensure all required variables are set.

3. **Start the Server**:
   ```bash
   python start.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the API**:
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/health

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/user` - Get current user
- `POST /api/auth/change-password` - Change password

### Chat
- `POST /api/chat` - Process chat message using RAG
- `GET /api/chat/conversations` - Get conversations for a bot
- `GET /api/chat/conversations/{id}` - Get conversation with messages

### Health
- `GET /api/health` - Application health check

## Environment Variables

All environment variables are defined in `.env`. Key variables include:

- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `QDRANT_URL` - Qdrant vector database URL
- `QDRANT_API_KEY` - Qdrant API key
- `AWS_ACCESS_KEY_ID` - AWS access key for Bedrock
- `AWS_SECRET_ACCESS_KEY` - AWS secret key for Bedrock

## Architecture

The application follows a layered architecture:

- **Routers**: Handle HTTP requests and responses
- **Services**: Business logic and external service integration
- **Models**: Pydantic schemas for request/response validation
- **Middleware**: Authentication and CORS handling
- **Config**: Environment configuration and database connections

## Development

### Adding New Endpoints

1. Define request/response models in `models/schemas.py`
2. Implement business logic in appropriate service class
3. Create router endpoints in `routers/`
4. Register router in `main.py`

### Logging

All requests are logged with correlation IDs for tracing. Use the logging utilities in `utils/logging.py` for consistent log formatting.

### Testing

Run tests using pytest:
```bash
pytest
```

## Deployment

The application can be deployed using:

- **Docker**: Build container and deploy
- **Cloud Platforms**: Deploy to AWS, GCP, Azure
- **Traditional Servers**: Use gunicorn or uvicorn

For production, ensure:
- Set `DEBUG=false` in environment
- Use proper database connection pooling
- Configure proper logging levels
- Set up monitoring and health checks