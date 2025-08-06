# AI Chatbot Platform - Start All Services Script (PowerShell)
# This script starts all the required services for the AI chatbot platform

Write-Host "Starting AI Chatbot Platform Services..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "Error: Docker is not running. Please start Docker and try again." -ForegroundColor Red
    exit 1
}

# Start Qdrant (Vector Database)
Write-Host "Starting Qdrant..." -ForegroundColor Yellow
Push-Location vector_db
docker-compose up -d
Pop-Location
Write-Host "✅ Qdrant started" -ForegroundColor Green

# Function to start a Python service
function Start-PythonService {
    param (
        [string]$ServiceName,
        [string]$ServiceFile,
        [int]$Port
    )
    
    Write-Host "Starting $ServiceName on port $Port..." -ForegroundColor Yellow
    
    # Create logs directory if it doesn't exist
    if (-not (Test-Path -Path "logs")) {
        New-Item -ItemType Directory -Path "logs" | Out-Null
    }
    
    # Start the service
    $ProcessInfo = Start-Process -FilePath "python" -ArgumentList $ServiceFile -RedirectStandardOutput "logs\$ServiceName.log" -RedirectStandardError "logs\${ServiceName}_error.log" -PassThru -NoNewWindow
    
    # Save the PID
    $ProcessInfo.Id | Out-File -FilePath "logs\$ServiceName.pid"
    
    Write-Host "✅ $ServiceName started (PID: $($ProcessInfo.Id))" -ForegroundColor Green
}

# Start Python microservices
Start-PythonService -ServiceName "crawler" -ServiceFile "crawler_service.py" -Port 8001
Start-PythonService -ServiceName "parser" -ServiceFile "parser_service.py" -Port 8002
Start-PythonService -ServiceName "embedding" -ServiceFile "embedding_service.py" -Port 8003
Start-PythonService -ServiceName "rag" -ServiceFile "rag_service.py" -Port 8004
Start-PythonService -ServiceName "realtime_crawl" -ServiceFile "realtime_crawl_service.py" -Port 8005

# Start API Gateway (Cloudflare Worker)
Write-Host "Starting API Gateway..." -ForegroundColor Yellow
Push-Location api

# Try to find npm path
$NpmPath = "npm"
try {
    $NpmPath = (Get-Command npm -ErrorAction Stop).Source
} catch {
    # Fallback to known location
    if (Test-Path "C:\nvm4w\nodejs\npm.cmd") {
        $NpmPath = "C:\nvm4w\nodejs\npm.cmd"
    }
}

Write-Host "Using npm from: $NpmPath" -ForegroundColor Yellow
$ApiProcess = Start-Process -FilePath $NpmPath -ArgumentList "run dev" -RedirectStandardOutput "..\logs\api.log" -RedirectStandardError "..\logs\api_error.log" -PassThru -NoNewWindow
$ApiProcess.Id | Out-File -FilePath "..\logs\api.pid"
Pop-Location
Write-Host "✅ API Gateway started (PID: $($ApiProcess.Id))" -ForegroundColor Green

# Start Dashboard
Write-Host "Starting Dashboard..." -ForegroundColor Yellow
Push-Location dashboard

# Try to find npm path
$NpmPath = "npm"
try {
    $NpmPath = (Get-Command npm -ErrorAction Stop).Source
} catch {
    # Fallback to known location
    if (Test-Path "C:\nvm4w\nodejs\npm.cmd") {
        $NpmPath = "C:\nvm4w\nodejs\npm.cmd"
    }
}

Write-Host "Using npm from: $NpmPath" -ForegroundColor Yellow
$DashboardProcess = Start-Process -FilePath $NpmPath -ArgumentList "start" -RedirectStandardOutput "..\logs\dashboard.log" -RedirectStandardError "..\logs\dashboard_error.log" -PassThru -NoNewWindow
$DashboardProcess.Id | Out-File -FilePath "..\logs\dashboard.pid"
Pop-Location
Write-Host "✅ Dashboard started (PID: $($DashboardProcess.Id))" -ForegroundColor Green

Write-Host ""
Write-Host "All services started successfully!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host "API Gateway:       http://localhost:8787"
Write-Host "Dashboard:         http://localhost:3000"
Write-Host "Crawler Service:   http://localhost:8001"
Write-Host "Parser Service:    http://localhost:8002"
Write-Host "Embedding Service: http://localhost:8003"
Write-Host "RAG Service:       http://localhost:8004"
Write-Host "Realtime Crawl:    http://localhost:8005"
Write-Host "Qdrant Dashboard:  http://localhost:6333/dashboard"
Write-Host ""
Write-Host "Log files are available in the logs/ directory"
Write-Host ""
Write-Host "To stop all services, run: .\stop_all_services.ps1" -ForegroundColor Yellow