@echo off
TITLE AI Chatbot Services

:: Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

cls

echo ========================================
echo       AI CHATBOT - SERVICE STARTUP      
echo ========================================

:: Check for Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [QDRANT] WARNING: Docker not found. Qdrant will not be started.
) else (
    echo [QDRANT] Starting Qdrant vector database...
    cd vector_db && docker-compose up -d && cd ..
    echo [QDRANT] Qdrant started at http://localhost:6333
)
timeout /t 2 >nul

echo.
echo ========================================
echo          STARTING MICROSERVICES         
echo ========================================

:: Check for Flask
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python 'flask' module not found. Run: pip install -r requirements.txt
)

:: Start services in background and log to files
python crawler_service.py > logs\crawler.log 2>&1 &
echo [Crawler Service]   logs\crawler.log (port 8001)
timeout /t 1 >nul

python parser_service.py > logs\parser.log 2>&1 &
echo [Parser Service]    logs\parser.log (port 8002)
timeout /t 1 >nul

python embedding_service.py > logs\embedding.log 2>&1 &
echo [Embedding Service] logs\embedding.log (port 8003)
timeout /t 1 >nul

python rag_service.py > logs\rag.log 2>&1 &
echo [RAG Service]       logs\rag.log (port 8004)
timeout /t 1 >nul

echo.
echo ========================================
echo          STARTING BACKEND API           
echo ========================================

cd api && npm run dev > ..\logs\api.log 2>&1 &
cd ..
echo [Cloudflare Worker API] logs\api.log (port 8787)
timeout /t 2 >nul

echo.
echo ========================================
echo             SERVICE SUMMARY             
echo ========================================
echo ✓ Qdrant vector database: http://localhost:6333
echo ✓ Crawler service:        http://localhost:8001
echo ✓ Parser service:         http://localhost:8002
echo ✓ Embedding service:      http://localhost:8003
echo ✓ RAG service:            http://localhost:8004
echo ✓ Cloudflare Worker API:  http://localhost:8787
echo.
echo API Documentation:        http://localhost:8787/api-docs
echo.
echo Logs are saved in the logs\ directory.
echo To view all logs in real time, see below.
echo To stop all services, press Ctrl+C here.
echo ========================================
echo.
echo Tailing all logs. Press Ctrl+C to stop everything.

:: Use PowerShell to tail logs (if available)
powershell -Command "Get-Content logs\*.log -Wait" 2>nul
if %errorlevel% neq 0 (
    echo PowerShell not available for log tailing.
    echo Check logs manually in the logs\ directory.
    pause
) 