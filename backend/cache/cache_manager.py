from typing import Dict, Any, Optional, Callable, Awaitable, TypeVar, Generic
import logging
import asyncio
import aioredis
from datetime import datetime, timedelta
import json
from functools import wraps
from pydantic import BaseModel

class CacheConfig(BaseModel):
    default_ttl: int = 300  # 5 minutes
    max_memory: int = 1024 * 1024 * 100  # 100MB
    cleanup_interval: int = 300  # 5 minutes
    redis_url: str = "redis://localhost:6379"
    compression_level: int = 6
    encryption_key: Optional[str] = None

class CacheManager:
    def __init__(self, config: CacheConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.redis_pool = None
        self.cleanup_task = None
        self.initialize_redis()
        self.start_cleanup()
    
    async def initialize_redis(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_pool = aioredis.from_url(
                self.config.redis_url,
                decode_responses=True
            )
            await self.redis_pool.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.error(f"Redis initialization failed: {str(e)}")
            raise
    
    async def start_cleanup(self) -> None:
        """Start cache cleanup task"""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self) -> None:
        """Periodic cache cleanup"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self.cleanup_expired()
                await self.cleanup_large_items()
            except Exception as e:
                self.logger.error(f"Cache cleanup failed: {str(e)}")
    
    async def cleanup_expired(self) -> None:
        """Clean up expired cache items"""
        try:
            keys = await self.redis_pool.keys("cache:*")
            for key in keys:
                ttl = await self.redis_pool.ttl(key)
                if ttl == -2:  # Key exists but has no TTL
                    await self.redis_pool.delete(key)
                    self.logger.info(f"Removed expired cache item: {key}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired items: {str(e)}")
    
    async def cleanup_large_items(self) -> None:
        """Clean up large cache items"""
        try:
            total_memory = 0
            keys = await self.redis_pool.keys("cache:*")
            
            for key in keys:
                size = await self.redis_pool.memory_usage(key)
                total_memory += size
                
                if total_memory > self.config.max_memory:
                    await self.redis_pool.delete(key)
                    self.logger.info(f"Removed large cache item: {key}")
                    break
        except Exception as e:
            self.logger.error(f"Failed to cleanup large items: {str(e)}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        try:
            data = await self.redis_pool.get(f"cache:{key}")
            if not data:
                return None
                
            # Decrypt if encryption is enabled
            if self.config.encryption_key:
                data = self._decrypt(data)
            
            # Decompress if compression is enabled
            if self.config.compression_level > 0:
                data = self._decompress(data)
            
            return json.loads(data)
            
        except Exception as e:
            self.logger.error(f"Cache get failed: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache"""
        try:
            # Convert to JSON
            data = json.dumps(value)
            
            # Compress if enabled
            if self.config.compression_level > 0:
                data = self._compress(data)
            
            # Encrypt if enabled
            if self.config.encryption_key:
                data = self._encrypt(data)
            
            # Set in Redis with TTL
            await self.redis_pool.setex(
                f"cache:{key}",
                ttl or self.config.default_ttl,
                data
            )
            
        except Exception as e:
            self.logger.error(f"Cache set failed: {str(e)}")
            raise
    
    async def delete(self, key: str) -> None:
        """Delete item from cache"""
        try:
            await self.redis_pool.delete(f"cache:{key}")
        except Exception as e:
            self.logger.error(f"Cache delete failed: {str(e)}")
            raise
    
    async def exists(self, key: str) -> bool:
        """Check if item exists in cache"""
        try:
            return bool(await self.redis_pool.exists(f"cache:{key}"))
        except Exception as e:
            self.logger.error(f"Cache exists check failed: {str(e)}")
            return False
    
    def cache(self, ttl: Optional[int] = None):
        """Cache decorator"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                key = self._generate_cache_key(func, args, kwargs)
                
                # Try to get from cache
                cached = await self.get(key)
                if cached is not None:
                    return cached
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Store in cache
                await self.set(key, result, ttl)
                
                return result
            
            return wrapper
        
        return decorator
    
    def _generate_cache_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function and arguments"""
        key_parts = [
            func.__name__,
            str(args),
            str(kwargs)
        ]
        return hashlib.sha256(
            "".join(key_parts).encode()
        ).hexdigest()
    
    def _compress(self, data: str) -> bytes:
        """Compress data"""
        import gzip
        return gzip.compress(data.encode(), self.config.compression_level)
    
    def _decompress(self, data: bytes) -> str:
        """Decompress data"""
        import gzip
        return gzip.decompress(data).decode()
    
    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt data"""
        from cryptography.fernet import Fernet
        fernet = Fernet(self.config.encryption_key)
        return fernet.encrypt(data)
    
    def _decrypt(self, data: bytes) -> bytes:
        """Decrypt data"""
        from cryptography.fernet import Fernet
        fernet = Fernet(self.config.encryption_key)
        return fernet.decrypt(data)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            stats = {
                "total_items": 0,
                "total_memory": 0,
                "hit_rate": 0,
                "miss_rate": 0,
                "expiry_count": 0,
                "large_items": 0
            }
            
            keys = await self.redis_pool.keys("cache:*")
            stats["total_items"] = len(keys)
            
            for key in keys:
                size = await self.redis_pool.memory_usage(key)
                stats["total_memory"] += size
                
                if size > self.config.max_memory:
                    stats["large_items"] += 1
                    
                ttl = await self.redis_pool.ttl(key)
                if ttl == -2:
                    stats["expiry_count"] += 1
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {str(e)}")
            return {"error": str(e)}
    
    async def shutdown(self) -> None:
        """Shutdown cache manager"""
        try:
            if self.cleanup_task:
                self.cleanup_task.cancel()
            if self.redis_pool:
                await self.redis_pool.close()
        except Exception as e:
            self.logger.error(f"Cache shutdown failed: {str(e)}")
