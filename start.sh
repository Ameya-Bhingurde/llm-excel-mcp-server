#!/bin/bash

# Start FastAPI backend on port 8001 in the background
uvicorn app.main:app --host 0.0.0.0 --port 8001 &

# Wait a moment for FastAPI to start
sleep 2

# Start Streamlit on the port Render assigns
streamlit run ui/app.py --server.port=$PORT --server.address=0.0.0.0
