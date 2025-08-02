#!/bin/bash
# Azure-optimized startup script

echo "🚀 Starting TasteTarget on Azure..."
echo "Environment: ${ENVIRONMENT:-production}"

# Set Azure-specific environment variables
export PORT=${PORT:-8000}
export BACKEND_PORT=8001
export FRONTEND_PORT=$PORT

echo "Backend Port: $BACKEND_PORT"
echo "Frontend Port: $FRONTEND_PORT"

# Function to check if port is ready
check_port() {
    local port=$1
    python -c "
import socket
import sys
try:
    sock = socket.socket()
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', $port))
    sock.close()
    sys.exit(0 if result == 0 else 1)
except:
    sys.exit(1)
"
}

# Function for cleanup
cleanup() {
    echo "🛑 Shutting down..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT EXIT

# Start FastAPI backend
echo "🚀 Starting FastAPI backend on port $BACKEND_PORT..."
python -m uvicorn main:app \
    --host=0.0.0.0 \
    --port=$BACKEND_PORT \
    --log-level=info \
    --workers=1 &

BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..60}; do
    if check_port $BACKEND_PORT; then
        echo "✅ Backend is ready!"
        break
    fi
    echo "⏳ Backend not ready yet ($i/60)..."
    sleep 2
done

# Test backend health
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
        sys.exit(1)
except:
    sys.exit(1)
" 2>/dev/null; then
        echo "✅ Backend is healthy!"
        break
    fi
    echo "⏳ Backend health check failed, retrying ($i/10)..."
    sleep 2
done

# Set API URL for Streamlit
export API_URL="http://localhost:$BACKEND_PORT"

# Start Streamlit frontend
echo "🚀 Starting Streamlit frontend on port $FRONTEND_PORT..."
streamlit run app.py \
    --server.port=$FRONTEND_PORT \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false \
    --server.headless=true &

FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Wait for frontend to be ready
echo "⏳ Waiting for frontend to be ready..."
for i in {1..60}; do
    if check_port $FRONTEND_PORT; then
        echo "✅ Frontend is ready!"
        break
    fi
    echo "⏳ Frontend not ready yet ($i/60)..."
    sleep 2
done

echo "🎉 TasteTarget is running!"
echo "📊 Frontend: http://localhost:$FRONTEND_PORT"
echo "🔧 Backend: http://localhost:$BACKEND_PORT"

# Keep both services running
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend stopped!"
        exit 1
    fi
    
    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ Frontend stopped!"
        exit 1
    fi
    
    sleep 30
done
