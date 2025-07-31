# To stop all services, press Ctrl+C in this terminal.

# Create logs directory if it doesn't exist
if (-not (Test-Path -Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

Clear-Host

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "      AI CHATBOT - SERVICE STARTUP      " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check for Docker
try {
    docker --version | Out-Null
    Write-Host "[QDRANT] Starting Qdrant vector database..." -ForegroundColor Yellow
    Set-Location -Path "vector_db"
    docker-compose up -d
    Set-Location -Path ".."
    Write-Host "[QDRANT] Qdrant started at http://localhost:6333" -ForegroundColor Green
} catch {
    Write-Host "[QDRANT] WARNING: Docker not found. Qdrant will not be started." -ForegroundColor Yellow
}
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "         STARTING MICROSERVICES         " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check for Flask
try {
    python -c "import flask" | Out-Null
} catch {
    Write-Host "[WARNING] Python 'flask' module not found. Run: pip install -r requirements.txt" -ForegroundColor Yellow
}

# Start services in background and log to files
Start-Job -ScriptBlock { python crawler_service.py } -Name "CrawlerService" | Out-Null
Start-Job -ScriptBlock { python parser_service.py } -Name "ParserService" | Out-Null
Start-Job -ScriptBlock { python embedding_service.py } -Name "EmbeddingService" | Out-Null
Start-Job -ScriptBlock { python rag_service.py } -Name "RAGService" | Out-Null

Write-Host "[Crawler Service]   logs\crawler.log (port 8001)" -ForegroundColor Green
Write-Host "[Parser Service]    logs\parser.log (port 8002)" -ForegroundColor Green
Write-Host "[Embedding Service] logs\embedding.log (port 8003)" -ForegroundColor Green
Write-Host "[RAG Service]       logs\rag.log (port 8004)" -ForegroundColor Green
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "         STARTING BACKEND API           " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Start API service
Set-Location -Path "api"
Start-Job -ScriptBlock { npm run dev } -Name "APIService" | Out-Null
Set-Location -Path ".."
Write-Host "[Cloudflare Worker API] logs\api.log (port 8787)" -ForegroundColor Green
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "             SERVICE SUMMARY            " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Qdrant vector database: http://localhost:6333" -ForegroundColor Green
Write-Host "✓ Crawler service:        http://localhost:8001" -ForegroundColor Green
Write-Host "✓ Parser service:         http://localhost:8002" -ForegroundColor Green
Write-Host "✓ Embedding service:      http://localhost:8003" -ForegroundColor Green
Write-Host "✓ RAG service:            http://localhost:8004" -ForegroundColor Green
Write-Host "✓ Cloudflare Worker API:  http://localhost:8787" -ForegroundColor Green
Write-Host ""
Write-Host "API Documentation:        http://localhost:8787/api-docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Logs are saved in the logs\ directory." -ForegroundColor Yellow
Write-Host "To view all logs in real time, see below." -ForegroundColor Yellow
Write-Host "To stop all services, press Ctrl+C here." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tailing all logs. Press Ctrl+C to stop everything." -ForegroundColor Cyan

# Tail all logs
try {
    Get-Content logs\*.log -Wait
} catch {
    Write-Host "Error tailing logs. Check logs manually in the logs\ directory." -ForegroundColor Red
    Read-Host "Press Enter to continue"
} 