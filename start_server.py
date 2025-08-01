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
    print(f"Environment: {os.environ.get('RAILWAY_ENVIRONMENT_NAME', 'local')}")
    
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
    
    # List Railway-specific variables
    railway_vars = [k for k in all_vars if "RAILWAY" in k.upper()]
    print(f"Railway variables: {railway_vars}")
    
    # List production-specific variables
    production_vars = [k for k in all_vars if "PRODUCTION" in k.upper()]
    print(f"Production variables: {production_vars}")
    
    # Check for alternative variable names
    alt_openai = os.environ.get("OPENAI_KEY") or os.environ.get("OPENAIKEY") or os.environ.get("OPENAI")
    alt_google = os.environ.get("GOOGLE_KEY") or os.environ.get("GOOGLEKEY") or os.environ.get("GOOGLE")
    print(f"Alternative OpenAI key present: {alt_openai is not None}")
    print(f"Alternative Google key present: {alt_google is not None}")
    
    # Try multiple variable name formats
    print("=== Trying Alternative Variable Names ===")
    
    # Check for various possible Railway variable names
    possible_openai_vars = [
        "OPENAI_API_KEY", "OPENAIKEY", "OPENAI_KEY", "OPENAI", 
        "OPENAIAPIKEY", "OPENAI_APIKEY", "OPENAIKEY",
        "RAILWAY_OPENAI_API_KEY", "RAILWAY_OPENAI_KEY", "RAILWAY_OPENAI",
        "PRODUCTION_OPENAI_API_KEY", "PRODUCTION_OPENAI_KEY", "PRODUCTION_OPENAI"
    ]
    
    possible_google_vars = [
        "GOOGLE_API_KEY", "GOOGLEKEY", "GOOGLE_KEY", "GOOGLE",
        "GOOGLEAPIKEY", "GOOGLE_APIKEY", "GOOGLEKEY",
        "RAILWAY_GOOGLE_API_KEY", "RAILWAY_GOOGLE_KEY", "RAILWAY_GOOGLE",
        "PRODUCTION_GOOGLE_API_KEY", "PRODUCTION_GOOGLE_KEY", "PRODUCTION_GOOGLE"
    ]
    
    found_openai = None
    found_google = None
    
    for var_name in possible_openai_vars:
        if os.environ.get(var_name):
            found_openai = os.environ.get(var_name)
            print(f"✅ Found OpenAI key as: {var_name}")
            break
    
    for var_name in possible_google_vars:
        if os.environ.get(var_name):
            found_google = os.environ.get(var_name)
            print(f"✅ Found Google key as: {var_name}")
            break
    
    # Set the standard names if found with different names
    if found_openai and not openai_key:
        os.environ["OPENAI_API_KEY"] = found_openai
        print("✅ Mapped alternative OpenAI key to OPENAI_API_KEY")
    
    if found_google and not google_key:
        os.environ["GOOGLE_API_KEY"] = found_google
        print("✅ Mapped alternative Google key to GOOGLE_API_KEY")
    
    # TEMPORARY: Set dummy API keys for Railway deployment testing
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Setting dummy OpenAI API key for testing")
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing"
    
    if not os.environ.get("GOOGLE_API_KEY"):
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