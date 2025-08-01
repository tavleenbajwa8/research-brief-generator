#!/usr/bin/env python3
"""
Startup script for Railway deployment.
Handles port configuration and starts the uvicorn server.
"""

import os
import sys
import uvicorn

def main():
    print("=== Starting Research Brief Generator v2 ===")
    
    # Get port from environment variable, default to 8000
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
    
    # Debug environment variables
    print("=== Environment Variables Debug ===")
    openai_key = os.environ.get("OPENAI_API_KEY")
    google_key = os.environ.get("GOOGLE_API_KEY")
    print(f"OPENAI_API_KEY present: {openai_key is not None}")
    print(f"GOOGLE_API_KEY present: {google_key is not None}")
    if openai_key:
        print(f"OPENAI_API_KEY length: {len(openai_key)}")
    if google_key:
        print(f"GOOGLE_API_KEY length: {len(google_key)}")
    
    # List all environment variables that contain "API"
    api_vars = {k: v[:10] + "..." if v and len(v) > 10 else v for k, v in os.environ.items() if "API" in k.upper()}
    print(f"All API-related env vars: {api_vars}")
    
    # List ALL environment variables to debug
    print("=== ALL Environment Variables ===")
    all_vars = list(os.environ.keys())
    print(f"Total env vars: {len(all_vars)}")
    print(f"Sample vars: {all_vars[:10]}")
    
    # Check for alternative variable names
    alt_openai = os.environ.get("OPENAI_KEY") or os.environ.get("OPENAIKEY") or os.environ.get("OPENAI")
    alt_google = os.environ.get("GOOGLE_KEY") or os.environ.get("GOOGLEKEY") or os.environ.get("GOOGLE")
    print(f"Alternative OpenAI key present: {alt_openai is not None}")
    print(f"Alternative Google key present: {alt_google is not None}")
    
    # TEMPORARY: Set dummy API keys for Railway deployment testing
    if not openai_key:
        print("⚠️  Setting dummy OpenAI API key for testing")
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing"
    
    if not google_key:
        print("⚠️  Setting dummy Google API key for testing") 
        os.environ["GOOGLE_API_KEY"] = "dummy-google-key-for-testing"
    
    # Check if app can be imported
    try:
        from app.main import app
        print("✅ App imported successfully")
    except Exception as e:
        print(f"❌ Failed to import app: {e}")
        import traceback
        traceback.print_exc()
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