"""
Middleware de Rate Limiting para controlar la velocidad de las peticiones
"""

import time
import asyncio
from typing import Dict, Optional
from fastapi import Request, HTTPException
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter basado en ventana deslizante"""
    
    def __init__(self, max_requests: int = 50, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
    
    async def is_allowed(self, client_ip: str) -> bool:
        """Verifica si la IP puede hacer una petición"""
        async with self._locks[client_ip]:
            current_time = time.time()
            
            # Limpiar requests antiguos
            while (self.requests[client_ip] and 
                   self.requests[client_ip][0] <= current_time - self.window_seconds):
                self.requests[client_ip].popleft()
            
            # Verificar límite
            if len(self.requests[client_ip]) >= self.max_requests:
                return False
            
            # Agregar nueva petición
            self.requests[client_ip].append(current_time)
            return True
    
    async def get_remaining_requests(self, client_ip: str) -> int:
        """Obtiene el número de peticiones restantes"""
        async with self._locks[client_ip]:
            current_time = time.time()
            
            # Limpiar requests antiguos
            while (self.requests[client_ip] and 
                   self.requests[client_ip][0] <= current_time - self.window_seconds):
                self.requests[client_ip].popleft()
            
            return max(0, self.max_requests - len(self.requests[client_ip]))
    
    async def get_reset_time(self, client_ip: str) -> float:
        """Obtiene el tiempo de reset de la ventana"""
        async with self._locks[client_ip]:
            if not self.requests[client_ip]:
                return time.time()
            
            return self.requests[client_ip][0] + self.window_seconds

# Instancia global del rate limiter
rate_limiter = RateLimiter(max_requests=30, window_seconds=60)

async def rate_limit_middleware(request: Request, call_next):
    """Middleware de rate limiting"""
    client_ip = request.client.host
    
    if not await rate_limiter.is_allowed(client_ip):
        remaining = await rate_limiter.get_remaining_requests(client_ip)
        reset_time = await rate_limiter.get_reset_time(client_ip)
        
        logger.warning(f"Rate limit exceeded for IP {client_ip}")
        
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Try again in {int(reset_time - time.time())} seconds",
                "retry_after": int(reset_time - time.time()),
                "remaining_requests": remaining
            }
        )
    
    response = await call_next(request)
    
    # Agregar headers de rate limiting
    remaining = await rate_limiter.get_remaining_requests(client_ip)
    reset_time = await rate_limiter.get_reset_time(client_ip)
    
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(reset_time))
    
    return response
