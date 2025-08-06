#!/bin/bash

# AI Chatbot Platform - Stop All Services Script
# This script stops all the services started by start_all_services.sh

echo "Stopping AI Chatbot Platform Services..."
echo "========================================"

# Function to stop a service by PID file
stop_service() {
  local service_name=$1
  local pid_file="logs/${service_name}.pid"
  
  if [ -f "$pid_file" ]; then
    local pid=$(cat "$pid_file")
    echo "Stopping $service_name (PID: $pid)..."
    
    if kill -0 $pid 2>/dev/null; then
      kill $pid
      sleep 1
      
      # Check if process is still running
      if kill -0 $pid 2>/dev/null; then
        echo "Process still running, forcing termination..."
        kill -9 $pid
      fi
      
      echo "✅ $service_name stopped"
    else
      echo "⚠️ $service_name was not running"
    fi
    
    rm "$pid_file"
  else
    echo "⚠️ No PID file found for $service_name"
  fi
}

# Stop all services
stop_service "dashboard"
stop_service "api"
stop_service "realtime_crawl"
stop_service "rag"
stop_service "embedding"
stop_service "parser"
stop_service "crawler"

# Stop Qdrant
echo "Stopping Qdrant..."
cd vector_db
docker-compose down
cd ..
echo "✅ Qdrant stopped"

echo ""
echo "All services stopped successfully!"