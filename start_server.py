#!/usr/bin/env python3
"""
Startup script for Railway deployment.
Handles port configuration and starts the uvicorn server.
"""

import os
import sys
import uvicorn

def main():
    print("=== Starting Research Brief Generator ===")
    
    # Get port from environment variable, default to 8000
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
    
    # Check if app can be imported
    try:
        from app.main import app
        print("✅ App imported successfully")
    except Exception as e:
        print(f"❌ Failed to import app: {e}")
        sys.exit(1)
    
    # Start the server
    print(f"🚀 Starting server on {host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()