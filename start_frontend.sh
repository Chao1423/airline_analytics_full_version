#!/bin/bash

# Start frontend development server

cd "$(dirname "$0")/frontend"

echo "🚀 Starting frontend development server..."
echo "📍 Address: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev

