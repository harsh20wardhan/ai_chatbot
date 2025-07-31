# Start all services including realtime crawl service
Write-Host "Starting AI Chatbot Services with Realtime Crawl..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python not found. Please install Python 3.8+ and try again." -ForegroundColor Red
    exit 1
}

# Check if required packages are installed
Write-Host "Checking required packages..." -ForegroundColor Yellow
$requiredPackages = @(
    "flask",
    "flask-socketio", 
    "sentence-transformers",
    "qdrant-client",
    "requests",
    "beautifulsoup4",
    "psycopg2-binary",
    "python-dotenv"
)

foreach ($package in $requiredPackages) {
    try {
        python -c "import $package" 2>$null
        Write-Host "✓ $package" -ForegroundColor Green
    } catch {
        Write-Host "✗ $package - Installing..." -ForegroundColor Yellow
        pip install $package
    }
}

# Create logs directory if it doesn't exist
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs"
}

# Function to start a service
function Start-Service {
    param(
        [string]$ServiceName,
        [string]$ScriptPath,
        [string]$LogFile
    )
    
    Write-Host "Starting $ServiceName..." -ForegroundColor Yellow
    
    # Check if the script exists
    if (!(Test-Path $ScriptPath)) {
        Write-Host "Error: $ScriptPath not found!" -ForegroundColor Red
        return $false
    }
    
    # Start the service in a new PowerShell window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python '$ScriptPath' 2>&1 | Tee-Object -FilePath 'logs/$LogFile'"
    
    # Wait a moment for the service to start
    Start-Sleep -Seconds 2
    
    Write-Host "✓ $ServiceName started" -ForegroundColor Green
    return $true
}

# Start services
$services = @(
    @{ Name = "Vector DB (Qdrant)"; Script = "vector_db/docker-compose.yml"; Log = "qdrant.log" },
    @{ Name = "Crawler Service"; Script = "crawler_service.py"; Log = "crawler.log" },
    @{ Name = "Embedding Service"; Script = "embedding_service.py"; Log = "embedding.log" },
    @{ Name = "Parser Service"; Script = "parser_service.py"; Log = "parser.log" },
    @{ Name = "RAG Service"; Script = "rag_service.py"; Log = "rag.log" },
    @{ Name = "Realtime Crawl Service"; Script = "realtime_crawl_service.py"; Log = "realtime_crawl.log" }
)

# Start Qdrant first
Write-Host "Starting Qdrant vector database..." -ForegroundColor Yellow
if (Test-Path "vector_db/docker-compose.yml") {
    Set-Location "vector_db"
    docker-compose up -d
    Set-Location ".."
    Write-Host "✓ Qdrant started" -ForegroundColor Green
    Start-Sleep -Seconds 5  # Wait for Qdrant to be ready
} else {
    Write-Host "Warning: Qdrant docker-compose.yml not found. Make sure Qdrant is running on port 6333" -ForegroundColor Yellow
}

# Start Python services
foreach ($service in $services[1..($services.Length-1)]) {
    Start-Service -ServiceName $service.Name -ScriptPath $service.Script -LogFile $service.Log
    Start-Sleep -Seconds 1
}

Write-Host "`nAll services started!" -ForegroundColor Green
Write-Host "`nService URLs:" -ForegroundColor Cyan
Write-Host "- Crawler Service: http://localhost:8001" -ForegroundColor White
Write-Host "- Embedding Service: http://localhost:8003" -ForegroundColor White
Write-Host "- Parser Service: http://localhost:8002" -ForegroundColor White
Write-Host "- RAG Service: http://localhost:8004" -ForegroundColor White
Write-Host "- Realtime Crawl Service: http://localhost:8005" -ForegroundColor White
Write-Host "- Qdrant Vector DB: http://localhost:6333" -ForegroundColor White

Write-Host "`nTo test the realtime crawl functionality:" -ForegroundColor Cyan
Write-Host "1. Open realtime_crawl_test.html in your browser" -ForegroundColor White
Write-Host "2. Enter a website URL and bot ID" -ForegroundColor White
Write-Host "3. Click 'Start Realtime Crawl'" -ForegroundColor White

Write-Host "`nTo stop all services, press Ctrl+C in each terminal window" -ForegroundColor Yellow
Write-Host "Or run: docker-compose down (in vector_db directory)" -ForegroundColor Yellow

# Keep the script running
Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 