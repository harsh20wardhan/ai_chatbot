#!/bin/bash

# =============================================================================
# FastAPI Backend Startup Script
# =============================================================================
# This script starts the FastAPI backend with proper configuration and
# health checks for all cloud services.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Main startup function
main() {
    echo "============================================================================="
    echo "                    FastAPI Backend Startup Script"
    echo "============================================================================="
    
    # Check if we're in the right directory
    if [ ! -f "main.py" ]; then
        print_error "main.py not found. Please run this script from the fastapi-backend directory."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_error ".env file not found. Please copy .env.example to .env and configure it."
        exit 1
    fi
    
    print_status "Starting FastAPI Backend..."
    
    # Check Python installation
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Python version: $python_version"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        print_warning "No virtual environment found. Creating one..."
        python3 -m venv venv
        print_success "Virtual environment created."
    fi
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        print_status "Activating virtual environment..."
        source .venv/bin/activate
    fi
    
    # Check if requirements are installed
    if [ -f "requirements.txt" ]; then
        print_status "Installing/updating dependencies..."
        pip install -r requirements.txt
        print_success "Dependencies installed."
    fi
    
    # Run configuration verification
    print_status "Verifying configuration..."
    if python3 verify_config.py; then
        print_success "Configuration verified."
    else
        print_error "Configuration verification failed. Please check your .env file."
        exit 1
    fi
    
    # Run cloud services test
    print_status "Testing cloud services connectivity..."
    if python3 test_cloud_services.py; then
        print_success "Cloud services test passed."
    else
        print_warning "Cloud services test failed. The app may still work but with limited functionality."
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Startup cancelled."
            exit 1
        fi
    fi
    
    # Check if port is available
    PORT=${PORT:-8000}
    if ! check_port $PORT; then
        print_error "Port $PORT is already in use. Please stop the existing service or change the PORT in .env"
        exit 1
    fi
    
    # Start the FastAPI application
    print_status "Starting FastAPI server on port $PORT..."
    echo "============================================================================="
    print_success "FastAPI Backend is starting up!"
    echo ""
    print_status "Server will be available at:"
    echo "  • Local:   http://localhost:$PORT"
    echo "  • Network: http://0.0.0.0:$PORT"
    echo ""
    print_status "API Documentation:"
    echo "  • Swagger UI: http://localhost:$PORT/docs"
    echo "  • ReDoc:      http://localhost:$PORT/redoc"
    echo ""
    print_status "Health Checks:"
    echo "  • Basic:    http://localhost:$PORT/health"
    echo "  • Detailed: http://localhost:$PORT/health/detailed"
    echo "  • Qdrant:   http://localhost:$PORT/health/qdrant"
    echo "  • Bedrock:  http://localhost:$PORT/health/bedrock"
    echo ""
    print_status "Press Ctrl+C to stop the server"
    echo "============================================================================="
    
    # Start the server with uvicorn
    if command_exists uvicorn; then
        uvicorn main:app --host 0.0.0.0 --port $PORT --reload
    else
        print_warning "uvicorn not found, trying with python -m uvicorn"
        python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT --reload
    fi
}

# Handle script interruption
cleanup() {
    print_status "Shutting down FastAPI Backend..."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Run main function
main "$@"