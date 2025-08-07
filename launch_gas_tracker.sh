#!/bin/bash
# Start Ethereum Gas Tracker UI

# Log function
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
  log "Error: Python 3 is required but not installed. Please install Python 3 and try again."
  exit 1
fi

# Check for required Python packages
python3 -c "import flask, flask_cors" &> /dev/null
if [ $? -ne 0 ]; then
  log "Installing required Python packages..."
  pip install flask flask-cors
fi

# Check if the gas API server is already running
netstat -tunlp 2>/dev/null | grep -q ":5001 "
if [ $? -eq 0 ]; then
  log "Gas API server is already running on port 5001"
else
  # Start the gas API server in the background
  log "Starting Gas API server..."
  python3 gas_api_server.py &
  GAS_API_PID=$!
  log "Gas API server started with PID: $GAS_API_PID"
  
  # Give the server time to start
  sleep 2
  
  # Check if the server started successfully
  if ! netstat -tunlp 2>/dev/null | grep -q ":5001 "; then
    log "Error: Failed to start Gas API server"
    exit 1
  fi
fi

# Try to open the web browser
log "Opening Gas Tracker in web browser..."
URL="http://localhost:5001"

# Try different browsers based on what's available
if command -v xdg-open &> /dev/null; then
  xdg-open $URL
elif command -v open &> /dev/null; then
  open $URL
elif command -v python3 &> /dev/null; then
  # Use Python to open a browser
  python3 -m webbrowser $URL
else
  log "No browser launcher detected. Please open $URL manually."
fi

log "Gas Tracker is now running"
log "Web interface: $URL"
log "Press Ctrl+C to stop the server"

# Wait for user to press Ctrl+C
if [ ! -z "$GAS_API_PID" ]; then
  # Only wait if we started the server in this script
  wait $GAS_API_PID
fi
