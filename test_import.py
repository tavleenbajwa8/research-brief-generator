#!/usr/bin/env python3
"""
Simple test to check if the app can be imported and started.
"""

import sys
import os

print("=== Testing App Import ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    print("Importing app.main...")
    from app.main import app
    print("✅ App imported successfully!")
    
    print("Testing app configuration...")
    print(f"App title: {app.title}")
    print(f"App version: {app.version}")
    
    print("✅ App configuration looks good!")
    
except Exception as e:
    print(f"❌ Error importing app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=== Import test completed successfully ===")