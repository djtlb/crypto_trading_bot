"""
Rate Limiter for API Server
===========================

Provides rate limiting functionality to protect API endpoints 
from excessive requests.
"""

import time
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimiter(BaseHTTPMiddleware):
    """
    Rate limiter middleware for FastAPI
    Limits the number of requests a client can make within a timeframe
    """
    
    def __init__(
        self,
        app,
        max_requests: int = 100,  # Max requests per window
        window_seconds: int = 60,  # Window size in seconds
        block_time_seconds: int = 300  # Block time in seconds if rate limit exceeded
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_time_seconds = block_time_seconds
        self.clients: Dict[str, List[Tuple[float, str]]] = {}  # IP -> [(timestamp, path)]
        self.blocked_clients: Dict[str, float] = {}  # IP -> timestamp when block expires
    
    async def dispatch(self, request: Request, call_next):
        """Process the request through rate limiting"""
        # Get client IP
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        path = request.url.path
        
        # Check if client is blocked
        if client_ip in self.blocked_clients:
            if current_time < self.blocked_clients[client_ip]:
                # Still blocked
                block_remaining = int(self.blocked_clients[client_ip] - current_time)
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Try again in {block_remaining} seconds."
                )
            else:
                # Block expired
                del self.blocked_clients[client_ip]
        
        # Initialize client record if not exists
        if client_ip not in self.clients:
            self.clients[client_ip] = []
        
        # Remove old requests outside the window
        window_start = current_time - self.window_seconds
        self.clients[client_ip] = [
            req for req in self.clients[client_ip] if req[0] >= window_start
        ]
        
        # Add current request
        self.clients[client_ip].append((current_time, path))
        
        # Check if rate limit exceeded
        if len(self.clients[client_ip]) > self.max_requests:
            # Block client
            self.blocked_clients[client_ip] = current_time + self.block_time_seconds
            # Clean up client history
            self.clients[client_ip] = []
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {self.block_time_seconds} seconds."
            )
        
        # Proceed with the request
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Get the first IP in case of multiple proxies
            return forwarded.split(",")[0].strip()
        
        # Fallback to the direct client address
        client_host = request.client.host if request.client else "unknown"
        return client_host
