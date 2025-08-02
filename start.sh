#!/bin/bash
# Azure-optimized startup script for TasteTarget (FastAPI + Streamlit)

set -e  # Exit on any error

echo "🚀 Starting TasteTarget on Azure..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Azure Port: ${PORT:-8000}"

# Function to check if a port is open
check_port() {
    local port=$1
    local max_attempts=$2
    local attempt=1
    
    echo "Checking if port $port is ready..."
    while [ $attempt -le $max_attempts ]; do
        if python -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', $port))
    sock.close()
    if result == 0:
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    sys.exit(1)
"; then
            echo "✅ Port $port is ready!"
            return 0
        fi
        echo "⏳ Port $port not ready yet (attempt $attempt/$max_attempts)..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ Port $port failed to become ready after $max_attempts attempts"
    return 1
}

# Function to handle cleanup on exit
cleanup() {
    echo "🛑 Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping FastAPI backend (PID: $BACKEND_PID)..."
        kill -TERM $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Stopping Streamlit frontend (PID: $FRONTEND_PID)..."
        kill -TERM $FRONTEND_PID 2>/dev/null || true
        wait $FRONTEND_PID 2>/dev/null || true
    fi
    echo "👋 Cleanup complete"
}

# Set up signal handlers for graceful shutdown
trap cleanup SIGTERM SIGINT EXIT

# Environment variable validation
echo "🔍 Validating environment variables..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
else
    echo "✅ OPENAI_API_KEY configured"
fi

if [ -z "$QLOO_API_KEY" ]; then
    echo "⚠️  Warning: QLOO_API_KEY not set"
else
    echo "✅ QLOO_API_KEY configured"
fi

if [ -z "$HUGGINGFACE_API_KEY" ]; then
    echo "⚠️  Warning: HUGGINGFACE_API_KEY not set"
else
    echo "✅ HUGGINGFACE_API_KEY configured"
fi

# Azure-specific port configuration
BACKEND_PORT=8001
FRONTEND_PORT=${PORT:-8000}  # Azure provides PORT env var

echo "🔧 Configuration:"
echo "  Backend Port: $BACKEND_PORT"
echo "  Frontend Port: $FRONTEND_PORT (Azure external port)"
echo "  Backend URL: http://localhost:$BACKEND_PORT"

# Start FastAPI backend
echo "🚀 Starting FastAPI backend on port $BACKEND_PORT..."
python -m uvicorn main:app \
    --host=0.0.0.0 \
    --port=$BACKEND_PORT \
    --log-level=info \
    --access-log \
    --workers=1 \
    --timeout-keep-alive=65 \
    --timeout-graceful-shutdown=30 &

BACKEND_PID=$!
echo "📝 FastAPI backend started with PID: $BACKEND_PID"

# Wait for backend to be ready
if ! check_port $BACKEND_PORT 30; then
    echo "❌ FastAPI backend failed to start properly"
    exit 1
fi

# Test backend health endpoint
echo "🩺 Testing backend health..."
for i in {1..10}; do
    if python -c "
import requests
import sys
try:
    response = requests.get('http://localhost:$BACKEND_PORT/health', timeout=5)
    if response.status_code == 200:
        print('✅ Backend health check passed')
        sys.exit(0)
    else:
        print(f'❌ Backend health check failed: {response.status_code}')
        sys.exit(1)
except Exception as e:
    print(f'❌ Backend health check error: {e}')
    sys.exit(1)
" 2>/dev/null; then
        echo "✅ Backend is healthy and ready!"
        break
    fi
    echo "⏳ Backend health check failed, retrying ($i/10)..."
    sleep 3
done

# Set API URL for Streamlit
export API_URL="http://localhost:$BACKEND_PORT"
echo "🔗 API_URL set to: $API_URL"

# Start Streamlit frontend
echo "🚀 Starting Streamlit frontend on port $FRONTEND_PORT..."

# Azure-optimized Streamlit configuration
streamlit run app.py \
    --server.port=$FRONTEND_PORT \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --server.enableWebsocketCompression=false \
    --browser.gatherUsageStats=false \
    --logger.level=info \
    --server.headless=true \
    --server.runOnSave=false \
    --client.showErrorDetails=false &

FRONTEND_PID=$!
echo "📝 Streamlit frontend started with PID: $FRONTEND_PID"

# Wait for frontend to be ready
if ! check_port $FRONTEND_PORT 30; then
    echo "❌ Streamlit frontend failed to start properly"
    exit 1
fi

echo "🎉 TasteTarget is now running on Azure!"
echo "📊 Frontend (Streamlit): http://localhost:$FRONTEND_PORT"
echo "🔧 Backend (FastAPI): http://localhost:$BACKEND_PORT"
echo "🩺 Health Check: http://localhost:$BACKEND_PORT/health"
echo "📚 API Docs: http://localhost:$BACKEND_PORT/docs"

# Keep the script running and monitor both processes
echo "👀 Monitoring services..."
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ FastAPI backend stopped unexpectedly!"
        exit 1
    fi
    
    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ Streamlit frontend stopped unexpectedly!"
        exit 1
    fi
    
    # Optional: Check if ports are still responsive
    if ! check_port $BACKEND_PORT 1 >/dev/null 2>&1; then
        echo "⚠️  Backend port $BACKEND_PORT not responsive"
    fi
    
    if ! check_port $FRONTEND_PORT 1 >/dev/null 2>&1; then
        echo "⚠️  Frontend port $FRONTEND_PORT not responsive"
    fi
    
    sleep 30  # Check every 30 seconds
done
