#!/bin/bash

# Start FastAPI backend in background
echo "Starting FastAPI backend..."
python -m uvicorn main:app --host=0.0.0.0 --port=8001 &
BACKEND_PID=$!

# Wait for backend to become responsive
echo "Waiting for backend to be ready..."
for i in {1..30}; do
  if nc -z localhost 8001; then
    echo "✅ Backend is up!"
    break
  fi
  echo "⏳ Backend not up yet ($i)..."
  sleep 1
done

# Start Streamlit frontend
echo "Starting Streamlit frontend..."
streamlit run app.py --server.port=8000 --server.address=0.0.0.0 --server.enableCORS=false
