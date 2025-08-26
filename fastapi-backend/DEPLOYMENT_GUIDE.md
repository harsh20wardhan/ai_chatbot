# FastAPI Backend Deployment & Integration Guide

This guide provides step-by-step instructions for deploying the FastAPI backend and integrating it with the existing React dashboard, replacing the Cloudflare Workers API.

## 🚀 **Quick Start (Development)**

### **1. Set Up FastAPI Backend**

```bash
# Navigate to the FastAPI backend directory
cd fastapi-backend

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your actual credentials

# Start the FastAPI server
python main.py
```

The FastAPI backend will be available at: `http://localhost:8000`

### **2. Update Dashboard Configuration**

```bash
# Run the automatic update script
python update_dashboard_api.py

# Or manually update the dashboard
cd ../dashboard

# Update API base URL in src/services/api.js
# Change: 'http://localhost:8787/api'
# To:     'http://localhost:8000/api'

# Start the dashboard
npm start
```

The dashboard will be available at: `http://localhost:6969`

## 📋 **Detailed Setup Instructions**

### **Prerequisites**

- **Python 3.9+** with pip
- **Node.js 16+** with npm
- **PostgreSQL** (Supabase)
- **Qdrant** vector database
- **AWS Bedrock** access
- **Ollama** for chat responses

### **External Services Setup**

#### **1. Qdrant Vector Database**

```bash
# Option 1: Docker (Recommended for development)
docker run -p 6333:6333 qdrant/qdrant

# Option 2: Cloud Qdrant
# Sign up at https://cloud.qdrant.io/
# Get your cluster URL and API key
```

#### **2. AWS Bedrock**

```bash
# Configure AWS credentials
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-west-2
```

#### **3. Ollama (for Chat)**

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the model
ollama pull deepseek-r1:8b

# Start Ollama server
ollama serve
```

### **Environment Configuration**

#### **FastAPI Backend (.env)**

```bash
# Application Settings
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Security
ALLOWED_HOSTS=*
ALLOWED_ORIGINS=*

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Database
SUPABASE_DB_HOST=db.your-project.supabase.co
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-password
SUPABASE_DB_PORT=5432

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-api-key-if-cloud

# AWS Bedrock
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Ollama
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=deepseek-r1:8b

# Performance
RATE_LIMIT_PER_MINUTE=60
MAX_REQUEST_SIZE=52428800
SLOW_REQUEST_THRESHOLD=1.0
LOG_LEVEL=INFO
```

#### **Dashboard (.env)**

```bash
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
```

## 🔧 **Dashboard Integration Updates**

### **Automatic Update (Recommended)**

```bash
cd fastapi-backend
python update_dashboard_api.py
```

### **Manual Updates**

If you prefer to update manually, modify `dashboard/src/services/api.js`:

#### **1. Base URL**
```javascript
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api', // Changed from 8787
  // ... rest of config
});
```

#### **2. Document Upload**
```javascript
// OLD
const response = await api.post('/documents/upload', formData);

// NEW
const response = await api.post('/documents', formData);
```

#### **3. Crawl Routes**
```javascript
// OLD
await api.post('/crawl/website', data);
await api.get(`/crawl/status/${jobId}`);

// NEW
await api.post('/crawl', data);
await api.get(`/crawl/${jobId}`);
```

#### **4. Widget Configuration**
```javascript
// OLD
await api.post(`/widget/${botId}/config`, configData);

// NEW
await api.put(`/widget/${botId}/config`, configData);
```

#### **5. Request Field Names**
```javascript
// Update crawl request fields
{
  bot_id: botId,           // Changed from botId
  max_pages: maxDepth,     // Changed from maxDepth
  exclude_patterns: excludePatterns  // Changed from excludePatterns
}
```

## 🧪 **Testing the Integration**

### **1. Health Checks**

```bash
# Test FastAPI backend health
curl http://localhost:8000/health

# Test detailed health (with all dependencies)
curl http://localhost:8000/health/detailed
```

### **2. API Compatibility Test**

```bash
# Run the test suite
cd fastapi-backend
python run_tests.py

# Run specific compatibility tests
pytest tests/test_api_compatibility.py -v
```

### **3. Dashboard Integration Test**

1. **Authentication Flow**
   - Register a new user
   - Login with credentials
   - Verify JWT token is received
   - Access protected routes

2. **Bot Management**
   - Create a new bot
   - Edit bot details
   - View bot list
   - Delete a bot

3. **Document Upload**
   - Upload a PDF document
   - Verify processing status
   - Check document appears in bot

4. **Website Crawling**
   - Start a crawl job
   - Monitor progress
   - Verify crawled content

5. **Chat Functionality**
   - Send a message to bot
   - Verify RAG response
   - Check conversation history

## 🚀 **Production Deployment**

### **1. FastAPI Backend Deployment**

#### **Option A: Docker Deployment**

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t fastapi-backend .
docker run -p 8000:8000 --env-file .env fastapi-backend
```

#### **Option B: Cloud Deployment (Railway, Render, etc.)**

```bash
# Install production dependencies
pip install gunicorn

# Create Procfile for deployment
echo "web: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:\$PORT" > Procfile

# Deploy to your preferred platform
```

#### **Option C: VPS Deployment**

```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip nginx

# Set up application
git clone your-repo
cd fastapi-backend
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/fastapi-backend.service

# Configure nginx reverse proxy
sudo nano /etc/nginx/sites-available/fastapi-backend
```

### **2. Dashboard Deployment**

```bash
# Build for production
cd dashboard
npm run build

# Deploy to static hosting (Netlify, Vercel, etc.)
# Or serve with nginx
```

### **3. Environment Variables for Production**

```bash
# FastAPI Backend
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
ALLOWED_ORIGINS=https://yourdashboard.com

# Dashboard
REACT_APP_API_URL=https://api.yourdomain.com/api
```

## 📊 **Monitoring and Maintenance**

### **1. Health Monitoring**

Set up monitoring for these endpoints:
- `GET /health` - Basic health check
- `GET /health/detailed` - Comprehensive health check
- `GET /health/database` - Database connectivity
- `GET /health/qdrant` - Vector database status
- `GET /health/bedrock` - AWS Bedrock status

### **2. Logging**

The FastAPI backend provides structured logging with:
- Request/response timing
- Error tracking with correlation IDs
- Service call monitoring
- Performance metrics

### **3. Performance Monitoring**

Monitor these metrics:
- Response times (target: <1s for most endpoints)
- Database connection pool usage
- Memory usage
- Error rates
- Rate limiting triggers

## 🔒 **Security Considerations**

### **Production Security Checklist**

- [ ] **HTTPS Only**: Ensure all traffic uses HTTPS
- [ ] **Environment Variables**: Never commit secrets to version control
- [ ] **CORS Configuration**: Restrict origins to your dashboard domain
- [ ] **Rate Limiting**: Configure appropriate rate limits
- [ ] **Input Validation**: All inputs are validated by Pydantic models
- [ ] **SQL Injection**: Using parameterized queries
- [ ] **File Upload Security**: File types and sizes are validated
- [ ] **Authentication**: JWT tokens are properly validated
- [ ] **Authorization**: Users can only access their own data

### **Security Headers**

The FastAPI backend includes security middleware:
- Trusted host validation
- Request size limiting
- Rate limiting per IP
- CORS protection
- Error message sanitization

## 🔄 **Migration Strategy**

### **Zero-Downtime Migration**

1. **Phase 1: Parallel Deployment**
   - Deploy FastAPI backend alongside Cloudflare Workers
   - Test all functionality thoroughly
   - Monitor performance and stability

2. **Phase 2: Gradual Traffic Shift**
   - Update dashboard to use FastAPI backend
   - Monitor for any issues
   - Keep Cloudflare Workers as fallback

3. **Phase 3: Complete Migration**
   - Verify all functionality works correctly
   - Monitor for 24-48 hours
   - Decommission Cloudflare Workers

### **Rollback Plan**

If issues arise:
1. Revert dashboard API configuration
2. Switch traffic back to Cloudflare Workers
3. Investigate and fix issues
4. Retry migration when ready

## 📞 **Support and Troubleshooting**

### **Common Issues**

1. **Database Connection Errors**
   - Verify Supabase credentials
   - Check network connectivity
   - Ensure database is accessible

2. **Qdrant Connection Issues**
   - Verify Qdrant is running
   - Check API key if using cloud
   - Ensure collections are created

3. **AWS Bedrock Access**
   - Verify AWS credentials
   - Check region configuration
   - Ensure Bedrock access is enabled

4. **Dashboard API Errors**
   - Check API base URL configuration
   - Verify CORS settings
   - Check browser network tab for errors

### **Debug Mode**

Enable debug mode for troubleshooting:

```bash
# FastAPI Backend
DEBUG=true
LOG_LEVEL=DEBUG

# Dashboard
REACT_APP_DEBUG=true
```

### **Log Analysis**

Check logs for common patterns:
- Authentication failures
- Database connection issues
- External service timeouts
- Rate limiting triggers
- Validation errors

## ✅ **Deployment Checklist**

### **Pre-Deployment**
- [ ] All environment variables configured
- [ ] External services (Qdrant, AWS, Ollama) accessible
- [ ] Database migrations completed (if any)
- [ ] Health checks passing
- [ ] Tests passing
- [ ] Dashboard API calls updated

### **Deployment**
- [ ] FastAPI backend deployed and accessible
- [ ] Dashboard updated and deployed
- [ ] DNS/routing configured
- [ ] SSL certificates installed
- [ ] Monitoring configured

### **Post-Deployment**
- [ ] All functionality tested end-to-end
- [ ] Performance metrics within acceptable ranges
- [ ] Error rates low
- [ ] User authentication working
- [ ] Data integrity verified
- [ ] Backup systems operational

## 🎉 **Success Metrics**

After successful deployment, you should see:

- **Improved Performance**: Faster API response times
- **Better Reliability**: Reduced cold starts and timeouts
- **Enhanced Monitoring**: Comprehensive health checks and logging
- **Simplified Architecture**: Single backend service instead of multiple microservices
- **Better Developer Experience**: Easier debugging and development

The FastAPI backend provides a robust, scalable, and maintainable replacement for the Cloudflare Workers API while maintaining full compatibility with your existing dashboard.