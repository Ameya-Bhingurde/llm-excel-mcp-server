#!/usr/bin/env python3
"""
Startup script to run both FastAPI backend and Streamlit frontend
"""
import os
import subprocess
import sys
import time

def main():
    print("=" * 60)
    print("Starting AutoXL Services")
    print("=" * 60)
    
    # Get the port from environment
    port = os.environ.get("PORT", "10000")
    
    # Start FastAPI backend on port 8001 in the background
    print("\n[1/2] Starting FastAPI backend on port 8001...")
    fastapi_process = subprocess.Popen([
        "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", "8001"
    ])
    
    # Wait for FastAPI to start
    print("Waiting for FastAPI to initialize...")
    time.sleep(3)
    
    # Start Streamlit on the port Render assigns
    print(f"\n[2/2] Starting Streamlit UI on port {port}...")
    streamlit_process = subprocess.Popen([
        "streamlit",
        "run",
        "ui/app.py",
        f"--server.port={port}",
        "--server.address=0.0.0.0",
        "--server.headless=true"
    ])
    
    print("\n" + "=" * 60)
    print("✅ Both services started successfully!")
    print("=" * 60)
    print(f"FastAPI:   http://127.0.0.1:8001")
    print(f"Streamlit: http://0.0.0.0:{port}")
    print("=" * 60 + "\n")
    
    # Wait for Streamlit to finish (it won't, so this keeps the script running)
    try:
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down services...")
        fastapi_process.terminate()
        streamlit_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
