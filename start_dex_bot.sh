#!/bin/bash
# filepath: /home/ubuntu/crypto_trading_bot/start_dex_bot.sh

# Activate virtual environment
source venv/bin/activate

# Find an available port starting from 8000
PORT=8000
while netstat -tuln | grep -q ":$PORT "; do
    echo "Port $PORT is in use, trying next port..."
    PORT=$((PORT+1))
done

echo "Starting DEX Trading Bot on port $PORT"
echo "Access the web interface at http://localhost:$PORT"
gunicorn -w 4 -b 0.0.0.0:$PORT dex_bot_app:app
