#!/bin/bash

echo "🚀 Starting Crypto Trading Bot - Complete Frontend & Backend"
echo "=================================================="

# Kill any existing servers on ports 8000 and 8001
echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "uvicorn.*8001" 2>/dev/null || true
sleep 2

# Navigate to project directory
cd /home/ubuntu/crypto_trading_bot

# Check if virtual environment exists
if [ ! -d "trading_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv trading_env
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source trading_env/bin/activate

# Install/upgrade requirements
echo "📋 Installing requirements..."
pip install -q --upgrade pip
pip install -q fastapi uvicorn websockets websocket-client requests numpy

echo ""
echo "🎯 Starting servers..."
echo "📊 Main API (port 8000): Dashboard, Gas API, DEX Analytics"  
echo "💬 Chat API (port 8001): WebSocket Chat Interface"
echo ""

# Start the main backend API server in background
echo "🚀 Starting main backend API server..."
python3 backend_api.py &
MAIN_PID=$!

# Wait a moment for main server to start
sleep 3

# Start the chat API server in background  
echo "💬 Starting chat API server..."
python3 api_chat.py &
CHAT_PID=$!

# Wait for servers to fully start
sleep 5

echo ""
echo "✅ SERVERS RUNNING!"
echo "=================================================="
echo "🌐 Dashboard: http://localhost:8000"
echo "⛽ Gas API: http://localhost:8000/api/gas"
echo "📈 DEX API: http://localhost:8000/api/dex/analytics"
echo "💬 Chat WebSocket: ws://localhost:8001/ws/chat"
echo "📊 System Status: http://localhost:8000/api/status"
echo ""
echo "💡 Open http://localhost:8000 in your browser to access the dashboard!"
echo ""
echo "🛑 Press Ctrl+C to stop all servers"
echo "=================================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $MAIN_PID 2>/dev/null || true
    kill $CHAT_PID 2>/dev/null || true
    pkill -f "uvicorn.*8000" 2>/dev/null || true
    pkill -f "uvicorn.*8001" 2>/dev/null || true
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup SIGINT SIGTERM

# Keep script running and monitor servers
while true; do
    if ! kill -0 $MAIN_PID 2>/dev/null; then
        echo "❌ Main API server stopped unexpectedly"
        break
    fi
    if ! kill -0 $CHAT_PID 2>/dev/null; then
        echo "❌ Chat API server stopped unexpectedly"  
        break
    fi
    sleep 5
done

cleanup
