#!/bin/bash

echo "🔁 Starting TasteTarget services..."

# Start FastAPI backend (port 8001)
echo "🚀 Starting FastAPI backend..."
python -m uvicorn main:app --host=0.0.0.0 --port=8001 --log-level error &
BACKEND_PID=$!

# Start Hugging Face Visual Generator (port 7860 or 8501 – pick an available one)
echo "🎨 Starting Hugging Face visual generator..."
python taste_target/taste-target-visual-generator/app.py &
VISUAL_GEN_PID=$!

# Wait for backend and visual gen to start (max 30s)
for i in {1..30}; do
  nc -z localhost 8001 && nc -z localhost 7860 && break
  echo "⏳ Waiting for services to be ready ($i)..."
  sleep 1
done

# Start Streamlit frontend (port $PORT for Azure compatibility)
echo "📊 Starting Streamlit frontend..."
streamlit run app.py \
  --server.port=$PORT \
  --server.address=0.0.0.0 \
  --server.enableCORS=false
