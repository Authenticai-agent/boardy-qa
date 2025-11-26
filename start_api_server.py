#!/usr/bin/env python3
"""Start the Boardy QA API server."""

import subprocess
import sys
import time
import requests
from pathlib import Path

def start_api_server():
    """Start the API server if not already running."""
    try:
        # Check if server is already running
        response = requests.get("http://localhost:8000/health", timeout=2)
        print("✅ API server is already running")
        return True
    except requests.exceptions.RequestException:
        # Server is not running, start it
        print("🚀 Starting API server...")
        
        # Start the server in background
        cmd = [
            sys.executable, "-c",
            "import uvicorn; from boardy_qa.web_api import app; "
            "uvicorn.run(app, host='0.0.0.0', port=8000, log_level='warning')"
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for server to start
        for i in range(10):
            try:
                response = requests.get("http://localhost:8000/health", timeout=1)
                print("✅ API server started successfully")
                return True
            except requests.exceptions.RequestException:
                time.sleep(1)
        
        print("❌ Failed to start API server")
        return False

if __name__ == "__main__":
    start_api_server()
