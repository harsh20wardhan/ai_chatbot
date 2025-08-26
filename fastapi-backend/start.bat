@echo off
REM =============================================================================
REM FastAPI Backend Startup Script (Windows)
REM =============================================================================
REM This script starts the FastAPI backend with proper configuration and
REM health checks for all cloud services.

setlocal enabledelayedexpansion

REM Colors for output (Windows doesn't support colors in batch easily, so we'll use text)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

echo =============================================================================
echo                     FastAPI Backend Startup Script
echo =============================================================================

REM Check if we're in the right directory
if not exist "main.py" (
    echo %ERROR% main.py not found. Please run this script from the fastapi-backend directory.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo %ERROR% .env file not found. Please copy .env.example to .env and configure it.
    pause
    exit /b 1
)

echo %INFO% Starting FastAPI Backend...

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% Python is not installed or not in PATH. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo %INFO% Python version: %python_version%

REM Check if virtual environment exists
if not exist "venv" if not exist ".venv" (
    echo %WARNING% No virtual environment found. Creating one...
    python -m venv venv
    echo %SUCCESS% Virtual environment created.
)

REM Activate virtual environment
if exist "venv" (
    echo %INFO% Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv" (
    echo %INFO% Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Check if requirements are installed
if exist "requirements.txt" (
    echo %INFO% Installing/updating dependencies...
    pip install -r requirements.txt
    echo %SUCCESS% Dependencies installed.
)

REM Run configuration verification
echo %INFO% Verifying configuration...
python verify_config.py
if errorlevel 1 (
    echo %ERROR% Configuration verification failed. Please check your .env file.
    pause
    exit /b 1
)
echo %SUCCESS% Configuration verified.

REM Run cloud services test
echo %INFO% Testing cloud services connectivity...
python test_cloud_services.py
if errorlevel 1 (
    echo %WARNING% Cloud services test failed. The app may still work but with limited functionality.
    set /p continue="Do you want to continue anyway? (y/N): "
    if /i not "!continue!"=="y" (
        echo %INFO% Startup cancelled.
        pause
        exit /b 1
    )
)
echo %SUCCESS% Cloud services test passed.

REM Check if port is available (simplified check for Windows)
set PORT=8000
if defined PORT (
    echo %INFO% Using port %PORT%
) else (
    set PORT=8000
)

REM Start the FastAPI application
echo %INFO% Starting FastAPI server on port %PORT%...
echo =============================================================================
echo %SUCCESS% FastAPI Backend is starting up!
echo.
echo %INFO% Server will be available at:
echo   • Local:   http://localhost:%PORT%
echo   • Network: http://0.0.0.0:%PORT%
echo.
echo %INFO% API Documentation:
echo   • Swagger UI: http://localhost:%PORT%/docs
echo   • ReDoc:      http://localhost:%PORT%/redoc
echo.
echo %INFO% Health Checks:
echo   • Basic:    http://localhost:%PORT%/health
echo   • Detailed: http://localhost:%PORT%/health/detailed
echo   • Qdrant:   http://localhost:%PORT%/health/qdrant
echo   • Bedrock:  http://localhost:%PORT%/health/bedrock
echo.
echo %INFO% Press Ctrl+C to stop the server
echo =============================================================================

REM Start the server with uvicorn
uvicorn main:app --host 0.0.0.0 --port %PORT% --reload
if errorlevel 1 (
    echo %WARNING% uvicorn command not found, trying with python -m uvicorn
    python -m uvicorn main:app --host 0.0.0.0 --port %PORT% --reload
)

pause