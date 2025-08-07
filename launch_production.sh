#!/bin/bash
# launch_production.sh - Launch the trading bot in production mode

# Set environment variables for production
export ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com,https://app.yourdomain.com"
export ENABLE_RATE_LIMIT=1
export RATE_LIMIT_MAX_REQUESTS=100
export RATE_LIMIT_WINDOW_SECONDS=60
export RATE_LIMIT_BLOCK_TIME=300
export LOG_LEVEL=info

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting Crypto Trading Bot in PRODUCTION mode..."
echo "------------------------------------------------"
echo "CORS Origins: $ALLOWED_ORIGINS"
echo "Rate Limiting: Enabled ($RATE_LIMIT_MAX_REQUESTS requests per $RATE_LIMIT_WINDOW_SECONDS seconds)"
echo "Log Level: $LOG_LEVEL"
echo "------------------------------------------------"

# Run the server with production settings
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4 --log-level $LOG_LEVEL --proxy-headers --forwarded-allow-ips '*' --ssl-keyfile /path/to/your/privkey.pem --ssl-certfile /path/to/your/fullchain.pem
