from typing import Dict, Any, Optional, Callable, Awaitable
import logging
import time
import asyncio
from functools import wraps
from fastapi import Request, Response, HTTPException
import aioredis
from pydantic import BaseModel

class RateLimitConfig(BaseModel):
    default_limit: int = 100  # requests per window
    window_size: int = 60  # seconds
    max_burst: int = 5
    retry_after: int = 1
    
    # Custom rate limits per endpoint
    custom_limits: Dict[str, int] = {
        '/api/trades': 1000,
        '/api/models': 500,
        '/api/predict': 200
    }

class RateLimiter:
    def __init__(self, redis_url: str):
        self.logger = logging.getLogger(__name__)
        self.redis_pool = None
        self.config = RateLimitConfig()
        self.initialize_redis(redis_url)
    
    async def initialize_redis(self, redis_url: str) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_pool = aioredis.from_url(redis_url, decode_responses=True)
            await self.redis_pool.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.error(f"Redis initialization failed: {str(e)}")
            raise
    
    async def get_rate_limit(self, request: Request) -> int:
        """Get rate limit for the request"""
        path = request.url.path
        return self.config.custom_limits.get(path, self.config.default_limit)
    
    async def get_window_key(self, request: Request) -> str:
        """Get Redis key for rate limiting window"""
        client_ip = request.client.host
        path = request.url.path
        timestamp = int(time.time() // self.config.window_size)
        return f"rate_limit:{client_ip}:{path}:{timestamp}"
    
    async def increment_counter(self, key: str) -> int:
        """Increment rate limit counter"""
        try:
            # Increment counter and set expiration
            await self.redis_pool.incr(key)
            await self.redis_pool.expire(key, self.config.window_size)
            return int(await self.redis_pool.get(key))
            
        except Exception as e:
            self.logger.error(f"Redis counter increment failed: {str(e)}")
            raise
    
    async def get_counter(self, key: str) -> int:
        """Get current counter value"""
        try:
            return int(await self.redis_pool.get(key))
            
        except Exception as e:
            self.logger.error(f"Redis counter get failed: {str(e)}")
            return 0
    
    def rate_limit(self, limit: Optional[int] = None):
        """Rate limiting decorator"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                try:
                    # Get rate limit
                    current_limit = limit if limit else await self.get_rate_limit(request)
                    
                    # Get window key
                    key = await self.get_window_key(request)
                    
                    # Get current counter
                    counter = await self.get_counter(key)
                    
                    # Check if limit exceeded
                    if counter >= current_limit:
                        raise HTTPException(
                            status_code=429,
                            detail="Too many requests",
                            headers={
                                "Retry-After": str(self.config.retry_after),
                                "X-RateLimit-Limit": str(current_limit),
                                "X-RateLimit-Remaining": "0",
                                "X-RateLimit-Reset": str(int(time.time() + self.config.window_size))
                            }
                        )
                    
                    # Increment counter
                    await self.increment_counter(key)
                    
                    # Execute function
                    response = await func(request, *args, **kwargs)
                    
                    # Add rate limit headers
                    counter = await self.get_counter(key)
                    response.headers["X-RateLimit-Limit"] = str(current_limit)
                    response.headers["X-RateLimit-Remaining"] = str(current_limit - counter)
                    response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.config.window_size))
                    
                    return response
                    
                except HTTPException as e:
                    raise
                except Exception as e:
                    self.logger.error(f"Rate limiting error: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail="Internal server error"
                    )
            
            return wrapper
        
        return decorator
    
    async def burst_limit(self, func: Callable):
        """Burst limiting decorator"""
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            try:
                # Get window key
                key = await self.get_window_key(request)
                
                # Get current counter
                counter = await self.get_counter(key)
                
                # Check if burst limit exceeded
                if counter >= self.config.max_burst:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests in burst",
                        headers={
                            "Retry-After": str(self.config.retry_after),
                            "X-Burst-Limit": str(self.config.max_burst),
                            "X-Burst-Remaining": "0",
                            "X-Burst-Reset": str(int(time.time() + self.config.window_size))
                        }
                    )
                
                return await func(request, *args, **kwargs)
                
            except HTTPException as e:
                raise
            except Exception as e:
                self.logger.error(f"Burst limiting error: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error"
                )
        
        return wrapper
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        try:
            stats = {
                'total_requests': 0,
                'rate_limited': 0,
                'burst_limited': 0,
                'current_windows': {}
            }
            
            # Get all rate limit keys
            keys = await self.redis_pool.keys("rate_limit:*")
            for key in keys:
                counter = await self.get_counter(key)
                stats['total_requests'] += counter
                
                # Get window info from key
                parts = key.split(':')
                ip = parts[2]
                path = parts[3]
                
                if ip not in stats['current_windows']:
                    stats['current_windows'][ip] = {}
                stats['current_windows'][ip][path] = counter
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get rate limiting stats: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to get rate limiting stats"
            )
