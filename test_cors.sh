#!/bin/bash
# test_cors.sh - Test the CORS configuration of the trading bot API

# Colors for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Set the base URL
API_URL="http://localhost:8000"
ALLOWED_ORIGIN="http://localhost:8000"
DISALLOWED_ORIGIN="http://evil-site.com"

echo -e "${BLUE}=== Testing CORS Configuration ===${NC}"
echo "This script will verify CORS settings are secure"
echo

# Test if the API is running
echo -e "${BLUE}Checking if API is running...${NC}"
health_check=$(curl -s -o /dev/null -w "%{http_code}" ${API_URL}/health)
if [ "$health_check" == "200" ]; then
    echo -e "${GREEN}✓ API is running (Status: $health_check)${NC}"
else
    echo -e "${RED}✗ API is not running (Status: $health_check)${NC}"
    echo "Please start the API server before running this test."
    exit 1
fi

# Test CORS preflight with allowed origin
echo -e "${BLUE}Testing CORS preflight with allowed origin...${NC}"
preflight=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS ${API_URL}/api/v1/status \
    -H "Origin: ${ALLOWED_ORIGIN}" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type")

if [ "$preflight" == "200" ] || [ "$preflight" == "204" ]; then
    echo -e "${GREEN}✓ CORS preflight from allowed origin successful (Status: $preflight)${NC}"
else
    echo -e "${RED}✗ CORS preflight from allowed origin failed (Status: $preflight)${NC}"
fi

# Test CORS with disallowed origin
echo -e "${BLUE}Testing CORS with disallowed origin...${NC}"
bad_origin=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS ${API_URL}/api/v1/status \
    -H "Origin: ${DISALLOWED_ORIGIN}" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type")

access_control_header=$(curl -s -I -X OPTIONS ${API_URL}/api/v1/status \
    -H "Origin: ${DISALLOWED_ORIGIN}" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type" | grep -i "Access-Control-Allow-Origin")

if [[ "$access_control_header" == *"${DISALLOWED_ORIGIN}"* ]]; then
    echo -e "${RED}✗ CORS allows disallowed origin - SECURITY ISSUE!${NC}"
    echo "   $access_control_header"
else
    echo -e "${GREEN}✓ CORS correctly blocks disallowed origin${NC}"
fi

# Test CORS with actual request
echo -e "${BLUE}Testing actual request with allowed origin...${NC}"
allowed_request=$(curl -s -o /dev/null -w "%{http_code}" ${API_URL}/api/v1/status \
    -H "Origin: ${ALLOWED_ORIGIN}")

if [ "$allowed_request" == "200" ] || [ "$allowed_request" == "204" ]; then
    echo -e "${GREEN}✓ Request from allowed origin successful (Status: $allowed_request)${NC}"
else
    echo -e "${RED}✗ Request from allowed origin failed (Status: $allowed_request)${NC}"
fi

# Get the allowed headers
echo -e "${BLUE}Checking allowed headers...${NC}"
allowed_headers=$(curl -s -I -X OPTIONS ${API_URL}/api/v1/status \
    -H "Origin: ${ALLOWED_ORIGIN}" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type" | grep -i "Access-Control-Allow-Headers")

if [[ -n "$allowed_headers" ]]; then
    echo -e "${GREEN}✓ Allowed headers:${NC}"
    echo "   $allowed_headers"
else
    echo -e "${RED}✗ No allowed headers found${NC}"
fi

# Get the allowed methods
echo -e "${BLUE}Checking allowed methods...${NC}"
allowed_methods=$(curl -s -I -X OPTIONS ${API_URL}/api/v1/status \
    -H "Origin: ${ALLOWED_ORIGIN}" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type" | grep -i "Access-Control-Allow-Methods")

if [[ -n "$allowed_methods" ]]; then
    echo -e "${GREEN}✓ Allowed methods:${NC}"
    echo "   $allowed_methods"
else
    echo -e "${RED}✗ No allowed methods found${NC}"
fi

echo
echo -e "${BLUE}=== CORS Testing Complete ===${NC}"
echo "Remember to verify these settings match your security requirements"
