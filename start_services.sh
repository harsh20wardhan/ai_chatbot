#!/bin/bash

# To stop all services, press Ctrl+C in this terminal.

mkdir -p logs

clear

echo "========================================"
echo "      AI CHATBOT - SERVICE STARTUP      "
echo "========================================"

# Check for Docker
if ! command -v docker &> /dev/null; then
  echo "[QDRANT] WARNING: Docker not found. Qdrant will not be started."
else
  echo "[QDRANT] Starting Qdrant vector database..."
  (cd vector_db && docker-compose up -d)
  echo "[QDRANT] Qdrant started at http://localhost:6333"
fi
sleep 2

echo
echo "========================================"
echo "         STARTING MICROSERVICES         "
echo "========================================"

# Check for Flask
python -c "import flask" 2>/dev/null || echo "[WARNING] Python 'flask' module not found. Run: pip install -r requirements.txt"

python crawler_service.py > logs/crawler.log 2>&1 &
echo "[Crawler Service]         logs/crawler.log (port 8001)"
sleep 1

python parser_service.py > logs/parser.log 2>&1 &
echo "[Parser Service]          logs/parser.log (port 8002)"
sleep 1

python embedding_service.py > logs/embedding.log 2>&1 &
echo "[Embedding Service]       logs/embedding.log (port 8003)"
sleep 1

python rag_service.py > logs/rag.log 2>&1 &
echo "[RAG Service]             logs/rag.log (port 8004)"
sleep 1

python realtime_crawl_service.py > logs/realtime_crawl.log 2>&1 &
echo "[Realtime Crawl Service]  logs/realtime_crawl.log (port 8005)"
sleep 1

echo
echo "========================================"
echo "         STARTING BACKEND API           "
echo "========================================"

(cd api && npm run dev > ../logs/api.log 2>&1 &)
echo "[Cloudflare Worker API]    logs/api.log (port 8787)"
sleep 2

echo
echo "========================================"
echo "             SERVICE SUMMARY            "
echo "========================================"
echo "✓ Qdrant vector database:      http://localhost:6333"
echo "✓ Crawler service:             http://localhost:8001"
echo "✓ Parser service:              http://localhost:8002"
echo "✓ Embedding service:           http://localhost:8003"
echo "✓ RAG service:                 http://localhost:8004"
echo "✓ Realtime Crawl service:      http://localhost:8005"
echo "✓ Cloudflare Worker API:       http://localhost:8787"
echo
echo "API Documentation:            http://localhost:8787/api-docs"
echo
echo "Logs are saved in the logs/ directory."
echo "To view all logs in real time, see below."
echo "To stop all services, press Ctrl+C here."
echo "========================================"
echo
echo "Tailing all logs. Press Ctrl+C to stop everything."
tail -f logs/*.log