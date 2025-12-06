#!/bin/bash

# NDVI Service Startup Script

echo "Starting NDVI Service..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your configuration before running the service."
fi

# Start the service
echo "Starting FastAPI server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

