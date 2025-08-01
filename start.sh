#!/bin/bash

echo "=== Starting Research Brief Generator ==="
echo "Current directory: $(pwd)"
echo "PORT: $PORT"
echo "RAILWAY_ENVIRONMENT: $RAILWAY_ENVIRONMENT"

# List files to debug
echo "=== Files in current directory ==="
ls -la

# Check if app directory exists
if [ ! -d "app" ]; then
    echo "ERROR: app directory not found!"
    exit 1
fi

# Check if main.py exists
if [ ! -f "app/main.py" ]; then
    echo "ERROR: app/main.py not found!"
    exit 1
fi

# Set default port if not provided
if [ -z "$PORT" ]; then
    PORT=8000
    echo "WARNING: PORT not set, using default: $PORT"
fi

echo "=== Starting uvicorn on port $PORT ==="
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level info 