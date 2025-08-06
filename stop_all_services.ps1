# AI Chatbot Platform - Stop All Services Script (PowerShell)
# This script stops all the services started by start_all_services.ps1

Write-Host "Stopping AI Chatbot Platform Services..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Function to stop a service by PID file
function Stop-Service-ByPid {
    param (
        [string]$ServiceName
    )
    
    $PidFile = "logs\$ServiceName.pid"
    
    if (Test-Path -Path $PidFile) {
        $Pid = Get-Content -Path $PidFile
        Write-Host "Stopping $ServiceName (PID: $Pid)..." -ForegroundColor Yellow
        
        try {
            # Check if process is running
            $Process = Get-Process -Id $Pid -ErrorAction SilentlyContinue
            
            if ($Process) {
                # Try to stop gracefully
                Stop-Process -Id $Pid -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 1
                
                # Check if still running and force if needed
                $Process = Get-Process -Id $Pid -ErrorAction SilentlyContinue
                if ($Process) {
                    Write-Host "Process still running, forcing termination..." -ForegroundColor Yellow
                    Stop-Process -Id $Pid -Force -ErrorAction SilentlyContinue
                }
                
                Write-Host "✅ $ServiceName stopped" -ForegroundColor Green
            } else {
                Write-Host "⚠️ $ServiceName was not running" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "⚠️ Error stopping $ServiceName: $_" -ForegroundColor Red
        }
        
        Remove-Item -Path $PidFile -ErrorAction SilentlyContinue
    } else {
        Write-Host "⚠️ No PID file found for $ServiceName" -ForegroundColor Yellow
    }
}

# Stop all services
Stop-Service-ByPid -ServiceName "dashboard"
Stop-Service-ByPid -ServiceName "api"
Stop-Service-ByPid -ServiceName "realtime_crawl"
Stop-Service-ByPid -ServiceName "rag"
Stop-Service-ByPid -ServiceName "embedding"
Stop-Service-ByPid -ServiceName "parser"
Stop-Service-ByPid -ServiceName "crawler"

# Stop Qdrant
Write-Host "Stopping Qdrant..." -ForegroundColor Yellow
Push-Location vector_db
docker-compose down
Pop-Location
Write-Host "✅ Qdrant stopped" -ForegroundColor Green

Write-Host ""
Write-Host "All services stopped successfully!" -ForegroundColor Green