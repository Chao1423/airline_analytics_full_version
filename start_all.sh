#!/bin/bash

# Start both frontend and backend servers

cd "$(dirname "$0")"

echo "🚀 Starting application..."
echo ""

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found"
    exit 1
fi

# Start backend (background)
echo "📦 Starting backend server..."
source venv/bin/activate
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
echo "📍 Address: http://127.0.0.1:8000"
echo "📖 API Documentation: http://127.0.0.1:8000/docs"
echo ""

# Wait for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend development server..."
cd ../frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo "📍 Address: http://localhost:3000"
echo ""

echo "============================================================"
echo "✅ Application started!"
echo "============================================================"
echo ""
echo "📝 Log files:"
echo "  - Backend: backend.log"
echo "  - Frontend: frontend.log"
echo ""
echo "🛑 Stop services:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  or run: ./stop_all.sh"
echo ""
echo "Press Ctrl+C will not stop services, use the commands above to stop"
echo ""

# Wait for user interrupt
wait

