from typing import Optional, Dict, Any
import logging
import json
from datetime import datetime, timedelta
import hashlib
import hmac
import base64
import jwt
from cryptography.fernet import Fernet
from fastapi import HTTPException, Request, Response
from pydantic import BaseModel
import redis
import aioredis

class SecurityConfig(BaseModel):
    jwt_secret: str
    encryption_key: str
    rate_limit: int = 100  # requests per minute
    max_retries: int = 3
    retry_delay: int = 1  # seconds
    api_key_salt: str = "quantum_trader_salt"
    password_salt: str = "quantum_trader_password_salt"

class SecurityManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = SecurityConfig(
            jwt_secret=os.getenv('JWT_SECRET', 'your-secret-key'),
            encryption_key=os.getenv('ENCRYPTION_KEY', 'your-encryption-key')
        )
        self.redis_pool = None
        self.initialize_redis()
    
    async def initialize_redis(self) -> None:
        """
        Initialize Redis connection
        """
        try:
            self.redis_pool = aioredis.from_url(
                "redis://localhost:6379",
                decode_responses=True
            )
            await self.redis_pool.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.error(f"Redis initialization failed: {str(e)}")
            raise
    
    def generate_api_key(self) -> str:
        """
        Generate a secure API key
        """
        timestamp = str(int(datetime.now().timestamp()))
        salted = f"{timestamp}{self.config.api_key_salt}"
        hashed = hashlib.sha256(salted.encode()).hexdigest()
        return f"qt_{hashed[:32]}"
    
    def verify_api_key(self, api_key: str) -> bool:
        """
        Verify API key validity
        """
        try:
            if not api_key.startswith("qt_"):
                return False
                
            # Check if key exists in Redis
            key_hash = api_key[3:]
            valid = await self.redis_pool.get(f"api_key:{key_hash}")
            return bool(valid)
            
        except Exception as e:
            self.logger.error(f"API key verification failed: {str(e)}")
            return False
    
    def encrypt_data(self, data: Dict) -> str:
        """
        Encrypt sensitive data
        """
        try:
            fernet = Fernet(self.config.encryption_key.encode())
            encrypted = fernet.encrypt(json.dumps(data).encode())
            return base64.urlsafe_b64encode(encrypted).decode()
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted: str) -> Dict:
        """
        Decrypt sensitive data
        """
        try:
            fernet = Fernet(self.config.encryption_key.encode())
            decoded = base64.urlsafe_b64decode(encrypted)
            decrypted = fernet.decrypt(decoded)
            return json.loads(decrypted.decode())
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def generate_jwt(self, user_id: str, role: str) -> str:
        """
        Generate JWT token
        """
        try:
            payload = {
                'user_id': user_id,
                'role': role,
                'exp': datetime.utcnow() + timedelta(hours=1)
            }
            return jwt.encode(payload, self.config.jwt_secret, algorithm='HS256')
            
        except Exception as e:
            self.logger.error(f"JWT generation failed: {str(e)}")
            raise
    
    def verify_jwt(self, token: str) -> Dict:
        """
        Verify JWT token
        """
        try:
            return jwt.decode(token, self.config.jwt_secret, algorithms=['HS256'])
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
            
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
    
    async def rate_limit(self, request: Request) -> None:
        """
        Rate limiting middleware
        """
        try:
            client_ip = request.client.host
            key = f"rate_limit:{client_ip}"
            
            # Increment request count
            await self.redis_pool.incr(key)
            
            # Set expiration (1 minute)
            await self.redis_pool.expire(key, 60)
            
            # Get current count
            count = int(await self.redis_pool.get(key))
            
            if count > self.config.rate_limit:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
                
        except Exception as e:
            self.logger.error(f"Rate limiting failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Rate limiting error"
            )
    
    def sanitize_input(self, data: Dict) -> Dict:
        """
        Sanitize input data to prevent injection attacks
        """
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Remove SQL injection patterns
                value = value.replace(';', '').replace('--', '')
                # Remove script tags
                value = value.replace('<script', '').replace('</script', '')
                # Remove command injection patterns
                value = value.replace('|', '').replace('&&', '').replace('||', '')
            sanitized[key] = value
        return sanitized
    
    async def audit_log(self, request: Request, response: Response) -> None:
        """
        Log security-relevant events
        """
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'path': request.url.path,
                'status': response.status_code,
                'ip': request.client.host,
                'user_agent': request.headers.get('user-agent', '')
            }
            
            # Store in Redis
            await self.redis_pool.rpush('audit_logs', json.dumps(log_entry))
            
        except Exception as e:
            self.logger.error(f"Audit logging failed: {str(e)}")
    
    def get_security_headers(self) -> Dict[str, str]:
        """
        Get security headers for responses
        """
        return {
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'"  # Adjust as needed
        }
