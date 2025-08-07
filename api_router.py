"""
API router configuration for versioned endpoints
================================================

Defines the API routers with versioning for the trading bot
"""

from fastapi import APIRouter

# Create routers for different API versions
api_v1 = APIRouter(prefix="/api/v1")
api_latest = APIRouter(prefix="/api")  # Alias for the latest API version

# Note: In the future, you can create a new api_v2 router and migrate endpoints gradually
