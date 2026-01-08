#!/bin/bash

# Check frontend-backend connection

echo "============================================================"
echo "Frontend-Backend Connection Diagnostics"
echo "============================================================"
echo ""

# Check if backend is running
echo "1. Checking backend service..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✅ Backend service is running (http://localhost:8000)"
    BACKEND_RESPONSE=$(curl -s http://localhost:8000/)
    echo "   Response: $BACKEND_RESPONSE"
else
    echo "   ❌ Backend service is not running or not accessible"
    echo "   Please run: cd backend && uvicorn main:app --host 127.0.0.1 --port 8000"
fi
echo ""

# Check if frontend is running
echo "2. Checking frontend service..."
if curl -s http://localhost:3000/ > /dev/null 2>&1; then
    echo "   ✅ Frontend service is running (http://localhost:3000)"
else
    echo "   ❌ Frontend service is not running or not accessible"
    echo "   Please run: cd frontend && npm run dev"
fi
echo ""

# Check API connection
echo "3. Testing API connection..."
API_RESPONSE=$(curl -s -H "Origin: http://localhost:3000" http://localhost:8000/airlines/top-rated)
if echo "$API_RESPONSE" | grep -q "status"; then
    echo "   ✅ API is accessible"
    DATA_COUNT=$(echo "$API_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('data', [])))" 2>/dev/null || echo "0")
    echo "   Returned $DATA_COUNT airlines"
else
    echo "   ❌ API is not accessible or returned error"
    echo "   Response: $API_RESPONSE"
fi
echo ""

# Check environment variables
echo "4. Checking environment variables..."
if [ -f "frontend/src/.env" ]; then
    echo "   ✅ frontend/src/.env exists"
    cat frontend/src/.env
else
    echo "   ❌ frontend/src/.env does not exist"
fi
echo ""

if [ -f "backend/.env" ]; then
    echo "   ✅ backend/.env exists"
    echo "   POSTGRES_DSN=$(cat backend/.env | grep POSTGRES_DSN | cut -d'=' -f2 | cut -d'@' -f1)@***"
else
    echo "   ❌ backend/.env does not exist"
fi
echo ""

echo "============================================================"
echo "Diagnostics completed"
echo "============================================================"

