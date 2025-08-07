#!/bin/bash
# test_api_cors.sh - Test API endpoint and CORS configuration

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Testing API and CORS Configuration ===${NC}"
echo "This script will test API endpoints and CORS settings"
echo ""

# Define test variables
API_HOST="localhost:8000"
ALLOWED_ORIGIN="http://localhost:8000"
DISALLOWED_ORIGIN="http://evil-site.com"

# Test a simple endpoint with allowed origin
echo -e "${BLUE}Testing endpoint with allowed origin...${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "Origin: $ALLOWED_ORIGIN" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  "http://$API_HOST/api/status")

if [ "$response" -eq 200 ]; then
    echo -e "${GREEN}✓ API access from allowed origin successful (Status: $response)${NC}"
else
    echo -e "${RED}✗ API access from allowed origin failed (Status: $response)${NC}"
fi

# Test CORS preflight with allowed origin
echo -e "${BLUE}Testing CORS preflight with allowed origin...${NC}"
preflight=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
  -H "Origin: $ALLOWED_ORIGIN" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  "http://$API_HOST/api/status")

if [ "$preflight" -eq 200 ] || [ "$preflight" -eq 204 ]; then
    echo -e "${GREEN}✓ CORS preflight from allowed origin successful (Status: $preflight)${NC}"
else
    echo -e "${RED}✗ CORS preflight from allowed origin failed (Status: $preflight)${NC}"
fi

# Test with disallowed origin
echo -e "${BLUE}Testing endpoint with disallowed origin...${NC}"
bad_response=$(curl -s -i -X GET \
  -H "Origin: $DISALLOWED_ORIGIN" \
  -H "Access-Control-Request-Method: GET" \
  "http://$API_HOST/api/status")

# Check if Access-Control-Allow-Origin is in the response
if echo "$bad_response" | grep -q "Access-Control-Allow-Origin: $DISALLOWED_ORIGIN"; then
    echo -e "${RED}✗ CORS allows disallowed origin - SECURITY ISSUE!${NC}"
else
    echo -e "${GREEN}✓ CORS correctly blocks disallowed origin${NC}"
fi

# Test rate limiting
echo -e "${BLUE}Testing rate limiting...${NC}"
echo "Making 5 rapid requests to test rate limiting..."

for i in {1..5}; do
    curl -s -o /dev/null -w "%{http_code}\n" \
      -H "Origin: $ALLOWED_ORIGIN" \
      "http://$API_HOST/api/status"
    # Small delay to see responses
    sleep 0.2
done

# Test WebSocket connection
echo -e "${BLUE}Testing WebSocket connection...${NC}"
# Generate a test token
TOKEN="test_token_$(date +%s)"

# Use websocat if available, otherwise suggest installation
if command -v websocat &> /dev/null; then
    echo "Attempting WebSocket connection with token..."
    websocat -v "ws://$API_HOST/ws?token=$TOKEN" --no-close &
    WS_PID=$!
    sleep 2
    kill $WS_PID 2>/dev/null
else
    echo -e "${RED}websocat not found. Cannot test WebSocket.${NC}"
    echo "Install with: cargo install websocat"
fi

echo ""
echo -e "${BLUE}=== API and CORS Testing Complete ===${NC}"
echo "Review the results above to confirm your configuration is secure."
