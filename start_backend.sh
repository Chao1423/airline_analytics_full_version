#!/bin/bash

# Start backend server

cd "$(dirname "$0")"
source venv/bin/activate
cd backend

echo "🚀 Starting backend server..."
echo "📍 Address: http://127.0.0.1:8000"
echo "📖 API Documentation: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --host 127.0.0.1 --port 8000

