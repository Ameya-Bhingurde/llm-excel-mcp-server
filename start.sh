#!/bin/bash

# Start FastAPI backend on port 8001 in the background
echo "Starting FastAPI backend on port 8001..."
uvicorn app.main:app --host 127.0.0.1 --port 8001 &

# Wait for FastAPI to start
sleep 3

# Start Streamlit on the port Render assigns
echo "Starting Streamlit UI on port $PORT..."
streamlit run ui/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
