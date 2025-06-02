from typing import Dict, Any, Optional, Callable, Awaitable
import logging
import asyncio
import aioredis
from datetime import datetime, timedelta
from pydantic import BaseModel
import hashlib
import secrets
import json
from fastapi import Request, Response, HTTPException, status
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes

class RateLimitConfig(BaseModel):
    redis_url: str = "redis://localhost:6379"
    global_rate_limit: int = 1000  # requests per minute
    burst_limit: int = 2000  # requests in burst window
    burst_window: int = 5  # seconds
    window_size: int = 60  # seconds
    token_bucket_size: int = 10000
    token_refill_rate: float = 100.0  # tokens per second
    leaky_bucket_size: int = 10000
    sliding_window_size: int = 1000
    sliding_window_interval: int = 1
    max_concurrent_requests: int = 100
    request_timeout: int = 5  # seconds
    max_queue_size: int = 1000
    queue_timeout: int = 30  # seconds
    max_retries: int = 3
    retry_delay: int = 1  # seconds
    ip_whitelist: List[str] = ["127.0.0.1", "::1"]
    ip_blacklist: List[str] = []
    user_rate_limit: Dict[str, int] = {
        "default": 100,
        "premium": 500,
        "enterprise": 1000
    }
    endpoint_rate_limit: Dict[str, int] = {
        "/api/v1/auth": 1000,
        "/api/v1/data": 500,
        "/api/v1/health": 10000
    }
    method_rate_limit: Dict[str, int] = {
        "GET": 1000,
        "POST": 500,
        "PUT": 200,
        "DELETE": 100
    }
    country_rate_limit: Dict[str, int] = {
        "US": 1000,
        "EU": 500,
        "AS": 300
    }
    organization_rate_limit: Dict[str, int] = {
        "default": 1000,
        "premium": 5000,
        "enterprise": 10000
    }
    encryption_key: str = "your-encryption-key"
    rsa_key_size: int = 2048

class AdvancedRateLimiter:
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.redis_pool = None
        self.initialize_redis()
        self.rsa_keys = {}
        self.initialize_rsa_keys()
        self.request_queue = asyncio.Queue()
        self.queue_processor = None
        
    def initialize_redis(self) -> None:
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
    
    def initialize_rsa_keys(self) -> None:
        """Initialize RSA keys for encryption"""
        try:
            # Generate RSA keys if not exist
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.config.rsa_key_size
            )
            public_key = private_key.public_key()
            
            self.rsa_keys['private'] = private_key
            self.rsa_keys['public'] = public_key
            
            # Store keys in Redis
            async with self.redis_pool as redis:
                await redis.set(
                    "rate_limiter:public_key",
                    public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ).decode()
                )
                await redis.set(
                    "rate_limiter:private_key",
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ).decode()
                )
            
        except Exception as e:
            self.logger.error(f"RSA key initialization failed: {str(e)}")
            raise
    
    async def start_queue_processor(self) -> None:
        """Start request queue processor"""
        async def process_queue():
            while True:
                try:
                    request = await asyncio.wait_for(
                        self.request_queue.get(),
                        timeout=self.config.queue_timeout
                    )
                    
                    # Process request
                    await self.process_request(request)
                    
                    # Mark task done
                    self.request_queue.task_done()
                    
                except asyncio.TimeoutError:
                    self.logger.warning("Request queue timeout")
                    continue
                except Exception as e:
                    self.logger.error(f"Queue processing failed: {str(e)}")
                    continue
        
        self.queue_processor = asyncio.create_task(process_queue())
    
    async def process_request(self, request: Request) -> None:
        """Process a single request"""
        try:
            # Validate IP
            if not await self.validate_ip(request.client.host):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="IP rate limit exceeded"
                )
            
            # Validate user
            if not await self.validate_user(request):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="User rate limit exceeded"
                )
            
            # Validate endpoint
            if not await self.validate_endpoint(request):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Endpoint rate limit exceeded"
                )
            
            # Validate method
            if not await self.validate_method(request.method):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Method rate limit exceeded"
                )
            
            # Validate country
            if not await self.validate_country(request):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Country rate limit exceeded"
                )
            
            # Validate organization
            if not await self.validate_organization(request):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Organization rate limit exceeded"
                )
            
            # Check token bucket
            if not await self.check_token_bucket(request):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Token bucket limit exceeded"
                )
            
            # Check leaky bucket
            if not await self.check_leaky_bucket(request):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Leaky bucket limit exceeded"
                )
            
            # Check sliding window
            if not await self.check_sliding_window(request):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Sliding window limit exceeded"
                )
            
            # Check concurrent requests
            if not await self.check_concurrent_requests(request):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Concurrent request limit exceeded"
                )
            
            # Process request
            await self.process_request_body(request)
            
        except Exception as e:
            self.logger.error(f"Request processing failed: {str(e)}")
            raise
    
    async def validate_ip(self, ip: str) -> bool:
        """Validate IP address against rate limits"""
        try:
            # Check whitelist
            if ip in self.config.ip_whitelist:
                return True
                
            # Check blacklist
            if ip in self.config.ip_blacklist:
                return False
                
            # Check rate limit
            key = f"rate_limit:ip:{ip}"
            count = await self.redis_pool.get(key)
            if count and int(count) >= self.config.ip_rate_limit:
                return False
                
            # Update rate limit
            await self.redis_pool.setex(
                key,
                self.config.window_size,
                (await self.redis_pool.get(key) or 0) + 1
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"IP validation failed: {str(e)}")
            return False
    
    async def validate_user(self, request: Request) -> bool:
        """Validate user against rate limits"""
        try:
            # Get user ID from token
            token = request.headers.get("Authorization")
            if not token:
                return False
                
            user_id = await self.get_user_id_from_token(token)
            if not user_id:
                return False
                
            # Get user tier
            tier = await self.get_user_tier(user_id)
            limit = self.config.user_rate_limit.get(tier, self.config.user_rate_limit["default"])
            
            # Check rate limit
            key = f"rate_limit:user:{user_id}"
            count = await self.redis_pool.get(key)
            if count and int(count) >= limit:
                return False
                
            # Update rate limit
            await self.redis_pool.setex(
                key,
                self.config.window_size,
                (await self.redis_pool.get(key) or 0) + 1
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"User validation failed: {str(e)}")
            return False
    
    async def validate_endpoint(self, request: Request) -> bool:
        """Validate endpoint against rate limits"""
        try:
            # Get endpoint
            endpoint = request.url.path
            
            # Get rate limit
            limit = self.config.endpoint_rate_limit.get(endpoint, self.config.global_rate_limit)
            
            # Check rate limit
            key = f"rate_limit:endpoint:{endpoint}"
            count = await self.redis_pool.get(key)
            if count and int(count) >= limit:
                return False
                
            # Update rate limit
            await self.redis_pool.setex(
                key,
                self.config.window_size,
                (await self.redis_pool.get(key) or 0) + 1
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Endpoint validation failed: {str(e)}")
            return False
    
    async def validate_method(self, method: str) -> bool:
        """Validate HTTP method against rate limits"""
        try:
            # Get rate limit
            limit = self.config.method_rate_limit.get(method, self.config.global_rate_limit)
            
            # Check rate limit
            key = f"rate_limit:method:{method}"
            count = await self.redis_pool.get(key)
            if count and int(count) >= limit:
                return False
                
            # Update rate limit
            await self.redis_pool.setex(
                key,
                self.config.window_size,
                (await self.redis_pool.get(key) or 0) + 1
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Method validation failed: {str(e)}")
            return False
    
    async def validate_country(self, request: Request) -> bool:
        """Validate country against rate limits"""
        try:
            # Get country from IP
            country = await self.get_country_from_ip(request.client.host)
            if not country:
                return False
                
            # Get rate limit
            limit = self.config.country_rate_limit.get(country, self.config.global_rate_limit)
            
            # Check rate limit
            key = f"rate_limit:country:{country}"
            count = await self.redis_pool.get(key)
            if count and int(count) >= limit:
                return False
                
            # Update rate limit
            await self.redis_pool.setex(
                key,
                self.config.window_size,
                (await self.redis_pool.get(key) or 0) + 1
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Country validation failed: {str(e)}")
            return False
    
    async def validate_organization(self, request: Request) -> bool:
        """Validate organization against rate limits"""
        try:
            # Get organization from token
            token = request.headers.get("Authorization")
            if not token:
                return False
                
            org = await self.get_organization_from_token(token)
            if not org:
                return False
                
            # Get rate limit
            limit = self.config.organization_rate_limit.get(org, self.config.global_rate_limit)
            
            # Check rate limit
            key = f"rate_limit:org:{org}"
            count = await self.redis_pool.get(key)
            if count and int(count) >= limit:
                return False
                
            # Update rate limit
            await self.redis_pool.setex(
                key,
                self.config.window_size,
                (await self.redis_pool.get(key) or 0) + 1
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Organization validation failed: {str(e)}")
            return False
    
    async def check_token_bucket(self, request: Request) -> bool:
        """Check token bucket algorithm"""
        try:
            # Get bucket key
            key = f"token_bucket:{request.client.host}"
            
            # Get current tokens
            tokens = await self.redis_pool.get(key)
            if not tokens:
                tokens = self.config.token_bucket_size
                await self.redis_pool.setex(
                    key,
                    self.config.window_size,
                    tokens
                )
            else:
                tokens = int(tokens)
            
            # Check if enough tokens
            if tokens < 1:
                return False
                
            # Update tokens
            await self.redis_pool.setex(
                key,
                self.config.window_size,
                tokens - 1
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Token bucket check failed: {str(e)}")
            return False
    
    async def check_leaky_bucket(self, request: Request) -> bool:
        """Check leaky bucket algorithm"""
        try:
            # Get bucket key
            key = f"leaky_bucket:{request.client.host}"
            
            # Get current water level
            water = await self.redis_pool.get(key)
            if not water:
                water = 0
                await self.redis_pool.setex(
                    key,
                    self.config.window_size,
                    water
                )
            else:
                water = int(water)
            
            # Check if bucket overflow
            if water >= self.config.leaky_bucket_size:
                return False
                
            # Update water level
            await self.redis_pool.setex(
                key,
                self.config.window_size,
                water + 1
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Leaky bucket check failed: {str(e)}")
            return False
    
    async def check_sliding_window(self, request: Request) -> bool:
        """Check sliding window algorithm"""
        try:
            # Get window key
            key = f"sliding_window:{request.client.host}"
            
            # Get current window
            window = await self.redis_pool.get(key)
            if not window:
                window = []
            else:
                window = json.loads(window)
            
            # Remove old requests
            now = datetime.now()
            window = [req for req in window if now - datetime.fromisoformat(req) < timedelta(seconds=self.config.window_size)]
            
            # Check if window full
            if len(window) >= self.config.sliding_window_size:
                return False
                
            # Add current request
            window.append(now.isoformat())
            
            # Update window
            await self.redis_pool.setex(
                key,
                self.config.window_size,
                json.dumps(window)
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Sliding window check failed: {str(e)}")
            return False
    
    async def check_concurrent_requests(self, request: Request) -> bool:
        """Check concurrent requests limit"""
        try:
            # Get concurrent key
            key = f"concurrent:{request.client.host}"
            
            # Get current count
            count = await self.redis_pool.get(key)
            if not count:
                count = 0
                await self.redis_pool.setex(
                    key,
                    self.config.request_timeout,
                    count
                )
            else:
                count = int(count)
            
            # Check if limit exceeded
            if count >= self.config.max_concurrent_requests:
                return False
                
            # Update count
            await self.redis_pool.setex(
                key,
                self.config.request_timeout,
                count + 1
            )
            
            # Create cleanup task
            asyncio.create_task(self.cleanup_concurrent(request.client.host))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Concurrent requests check failed: {str(e)}")
            return False
    
    async def cleanup_concurrent(self, ip: str) -> None:
        """Cleanup concurrent request count"""
        try:
            await asyncio.sleep(self.config.request_timeout)
            key = f"concurrent:{ip}"
            count = await self.redis_pool.get(key)
            if count:
                await self.redis_pool.setex(
                    key,
                    self.config.request_timeout,
                    max(0, int(count) - 1)
                )
        except Exception as e:
            self.logger.error(f"Concurrent cleanup failed: {str(e)}")
    
    async def process_request_body(self, request: Request) -> None:
        """Process request body"""
        try:
            # Get request body
            body = await request.body()
            
            # Validate request size
            if len(body) > self.config.max_request_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Request body too large"
                )
            
            # Process request
            # Implementation depends on your application
            pass
            
        except Exception as e:
            self.logger.error(f"Request body processing failed: {str(e)}")
            raise
    
    async def get_user_id_from_token(self, token: str) -> Optional[str]:
        """Get user ID from token"""
        try:
            # Decrypt token
            decrypted = self.decrypt_data(token)
            if not decrypted:
                return None
                
            # Get user ID from decrypted data
            data = json.loads(decrypted)
            return data.get('user_id')
            
        except Exception as e:
            self.logger.error(f"User ID lookup failed: {str(e)}")
            return None
    
    async def get_user_tier(self, user_id: str) -> str:
        """Get user tier"""
        try:
            # Get user tier from Redis
            key = f"user:{user_id}:tier"
            tier = await self.redis_pool.get(key)
            if not tier:
                return "default"
                
            return tier
            
        except Exception as e:
            self.logger.error(f"User tier lookup failed: {str(e)}")
            return "default"
    
    async def get_country_from_ip(self, ip: str) -> Optional[str]:
        """Get country from IP address"""
        try:
            # Check Redis cache first
            key = f"ip:{ip}:country"
            country = await self.redis_pool.get(key)
            if country:
                return country
                
            # Get country from external service
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://ipapi.co/{ip}/json/") as response:
                    if response.status == 200:
                        data = await response.json()
                        country = data.get('country')
                        if country:
                            # Cache result
                            await self.redis_pool.setex(
                                key,
                                3600,  # 1 hour cache
                                country
                            )
                            return country
            
            return None
            
        except Exception as e:
            self.logger.error(f"Country lookup failed: {str(e)}")
            return None
    
    async def get_organization_from_token(self, token: str) -> Optional[str]:
        """Get organization from token"""
        try:
            # Decrypt token
            decrypted = self.decrypt_data(token)
            if not decrypted:
                return None
                
            # Get organization from decrypted data
            data = json.loads(decrypted)
            return data.get('organization')
            
        except Exception as e:
            self.logger.error(f"Organization lookup failed: {str(e)}")
            return None
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            # Generate random IV
            iv = secrets.token_bytes(16)
            
            # Generate key from config
            key = hashlib.pbkdf2_hmac(
                'sha256',
                self.config.encryption_key.encode(),
                iv,
                100000
            )
            
            # Encrypt data
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            
            # Pad data
            padded_data = data.encode() + b' ' * (16 - len(data) % 16)
            
            # Encrypt
            encrypted = encryptor.update(padded_data) + encryptor.finalize()
            
            # Return base64 encoded result
            return base64.b64encode(iv + encrypted).decode()
            
        except Exception as e:
            self.logger.error(f"Data encryption failed: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted: str) -> str:
        """Decrypt sensitive data"""
        try:
            # Decode base64
            data = base64.b64decode(encrypted)
            
            # Extract IV
            iv = data[:16]
            encrypted_data = data[16:]
            
            # Generate key from config
            key = hashlib.pbkdf2_hmac(
                'sha256',
                self.config.encryption_key.encode(),
                iv,
                100000
            )
            
            # Decrypt data
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            
            # Decrypt
            decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Return decoded string
            return decrypted.decode().rstrip()
            
        except Exception as e:
            self.logger.error(f"Data decryption failed: {str(e)}")
            raise
