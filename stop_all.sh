#!/bin/bash

# Stop all running backend and frontend services

echo "🛑 Stopping all services..."

# Stop backend (uvicorn)
pkill -f "uvicorn main:app" && echo "✅ Backend stopped" || echo "⚠️  Backend not running"

# Stop frontend (vite)
pkill -f "vite" && echo "✅ Frontend stopped" || echo "⚠️  Frontend not running"

# Clean log files (optional)
# rm -f backend.log frontend.log

echo ""
echo "✅ All services stopped"

