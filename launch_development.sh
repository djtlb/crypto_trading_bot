#!/bin/bash
# launch_development.sh - Launch the trading bot in development mode

# Set environment variables for development
export ALLOWED_ORIGINS="http://localhost:8000,http://127.0.0.1:8000"
export ENABLE_RATE_LIMIT=0
export LOG_LEVEL=debug

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting Crypto Trading Bot in DEVELOPMENT mode..."
echo "------------------------------------------------"
echo "CORS Origins: $ALLOWED_ORIGINS"
echo "Rate Limiting: Disabled"
echo "Log Level: $LOG_LEVEL (using lowercase as required by uvicorn)"
echo "------------------------------------------------"

# Run the server with hot reload for development
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload --log-level $LOG_LEVEL || {
    echo -e "\n\033[0;31mError: Failed to start the server. Check that LOG_LEVEL is one of: 'critical', 'error', 'warning', 'info', 'debug', 'trace' (lowercase required).\033[0m"
    exit 1
}
