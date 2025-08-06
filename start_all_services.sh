#!/bin/bash

# AI Chatbot Platform - Start All Services Script
# This script starts all the required services for the AI chatbot platform

echo "Starting AI Chatbot Platform Services..."
echo "========================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Start Qdrant (Vector Database)
echo "Starting Qdrant..."
cd vector_db
docker-compose up -d
cd ..
echo "✅ Qdrant started"

# Function to start a Python service
start_python_service() {
  local service_name=$1
  local service_file=$2
  local port=$3
  
  echo "Starting $service_name on port $port..."
  python $service_file > logs/${service_name}.log 2>&1 &
  echo $! > logs/${service_name}.pid
  echo "✅ $service_name started (PID: $(cat logs/${service_name}.pid))"
}

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Python microservices
start_python_service "crawler" "crawler_service.py" 8001
start_python_service "parser" "parser_service.py" 8002
start_python_service "embedding" "embedding_service.py" 8003
start_python_service "rag" "rag_service.py" 8004
start_python_service "realtime_crawl" "realtime_crawl_service.py" 8005

# Start API Gateway (Cloudflare Worker)
echo "Starting API Gateway..."
cd api
# Use full path to npm to avoid command not found errors
NPM_PATH=$(which npm 2>/dev/null || echo "/c/nvm4w/nodejs/npm")
$NPM_PATH run dev > ../logs/api.log 2>&1 &
echo $! > ../logs/api.pid
cd ..
echo "✅ API Gateway started (PID: $(cat logs/api.pid))"

# Start Dashboard
echo "Starting Dashboard..."
cd dashboard
# Use full path to npm to avoid command not found errors
NPM_PATH=$(which npm 2>/dev/null || echo "/c/nvm4w/nodejs/npm")
$NPM_PATH start > ../logs/dashboard.log 2>&1 &
echo $! > ../logs/dashboard.pid
cd ..
echo "✅ Dashboard started (PID: $(cat logs/dashboard.pid))"

echo ""
echo "All services started successfully!"
echo "=================================="
echo "API Gateway:       http://localhost:8787"
echo "Dashboard:         http://localhost:3000"
echo "Crawler Service:   http://localhost:8001"
echo "Parser Service:    http://localhost:8002"
echo "Embedding Service: http://localhost:8003"
echo "RAG Service:       http://localhost:8004"
echo "Realtime Crawl:    http://localhost:8005"
echo "Qdrant Dashboard:  http://localhost:6333/dashboard"
echo ""
echo "Log files are available in the logs/ directory"
echo ""
echo "To stop all services, run: ./stop_all_services.sh"