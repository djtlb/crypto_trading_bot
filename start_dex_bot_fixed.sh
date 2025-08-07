#!/bin/bash
# filepath: /home/ubuntu/crypto_trading_bot/start_dex_bot_fixed.sh

echo "🚀 Starting DEX Trading Bot..."

# Activate virtual environment
source venv/bin/activate || { echo "❌ Failed to activate virtual environment"; exit 1; }

# Find an available port starting from 8000
PORT=8000
MAX_PORT=8100
while sudo ss -tulpn | grep ":$PORT " > /dev/null && [ $PORT -lt $MAX_PORT ]; do
    echo "🔄 Port $PORT is in use, trying next port..."
    PORT=$((PORT+1))
done

if [ $PORT -eq $MAX_PORT ]; then
    echo "❌ Could not find an available port between 8000 and $MAX_PORT"
    exit 1
fi

echo "✅ Found available port: $PORT"
echo "🌐 Starting server on http://localhost:$PORT"

# Start the server in the foreground for easier debugging
gunicorn -w 4 -b 0.0.0.0:$PORT dex_bot_app:app
