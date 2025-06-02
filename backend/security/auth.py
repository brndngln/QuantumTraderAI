from typing import Dict, Any, Optional, List
import logging
import jwt
import bcrypt
from datetime import datetime, timedelta
import asyncio
import aioredis
from pydantic import BaseModel
from fastapi import Request, Response, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

class AuthConfig(BaseModel):
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "RS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_salt_rounds: int = 12
    token_issuer: str = "quantum_trader"
    token_audience: str = "quantum_trader_api"
    redis_url: str = "redis://localhost:6379"

class AuthError(Exception):
    def __init__(self, detail: str, status_code: int = 401):
        self.detail = detail
        self.status_code = status_code

class AuthService:
    def __init__(self, config: AuthConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.redis_pool = None
        self.initialize_redis()
        self.initialize_keys()
    
    async def initialize_redis(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_pool = aioredis.from_url(self.config.redis_url, decode_responses=True)
            await self.redis_pool.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            raise AuthError(f"Redis initialization failed: {str(e)}")
    
    def initialize_keys(self) -> None:
        """Initialize JWT keys"""
        try:
            # Generate RSA keys if they don't exist
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            self.private_key = private_key
            self.public_key = private_key.public_key()
            
            # Store keys in Redis
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            await self.redis_pool.set('jwt_private_key', private_pem.decode())
            await self.redis_pool.set('jwt_public_key', public_pem.decode())
            
        except Exception as e:
            raise AuthError(f"Key generation failed: {str(e)}")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(self.config.password_salt_rounds)).decode()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify hashed password"""
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
    
    async def create_tokens(self, user_id: str, roles: List[str]) -> Dict[str, str]:
        """Create access and refresh tokens"""
        try:
            # Create access token
            access_token_expires = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
            access_token = self.create_jwt(
                user_id=user_id,
                roles=roles,
                expires=access_token_expires
            )
            
            # Create refresh token
            refresh_token_expires = datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days)
            refresh_token = self.create_jwt(
                user_id=user_id,
                roles=roles,
                expires=refresh_token_expires,
                token_type="refresh"
            )
            
            # Store refresh token in Redis
            await self.redis_pool.setex(
                f"refresh_token:{user_id}",
                int(self.config.refresh_token_expire_days * 24 * 60 * 60),
                refresh_token
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.config.access_token_expire_minutes * 60
            }
            
        except Exception as e:
            raise AuthError(f"Token creation failed: {str(e)}")
    
    def create_jwt(self, user_id: str, roles: List[str], expires: datetime, token_type: str = "access") -> str:
        """Create JWT token"""
        payload = {
            "sub": user_id,
            "roles": roles,
            "exp": expires,
            "iat": datetime.utcnow(),
            "iss": self.config.token_issuer,
            "aud": self.config.token_audience,
            "token_type": token_type
        }
        
        return jwt.encode(
            payload,
            self.private_key,
            algorithm=self.config.jwt_algorithm
        )
    
    async def verify_jwt(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.config.jwt_algorithm],
                issuer=self.config.token_issuer,
                audience=self.config.token_audience
            )
            
            if payload.get("token_type") != token_type:
                raise AuthError("Invalid token type")
                
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthError("Token has expired", 401)
        except jwt.InvalidTokenError:
            raise AuthError("Invalid token", 401)
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token"""
        try:
            # Verify refresh token
            payload = await self.verify_jwt(refresh_token, "refresh")
            user_id = payload["sub"]
            roles = payload["roles"]
            
            # Check if refresh token exists in Redis
            stored_token = await self.redis_pool.get(f"refresh_token:{user_id}")
            if not stored_token or stored_token != refresh_token:
                raise AuthError("Invalid refresh token", 401)
            
            # Create new tokens
            return await self.create_tokens(user_id, roles)
            
        except Exception as e:
            raise AuthError(f"Token refresh failed: {str(e)}")
    
    async def get_current_user(self, request: Request) -> Dict[str, Any]:
        """Get current authenticated user"""
        try:
            authorization = request.headers.get("Authorization")
            if not authorization:
                raise AuthError("Missing Authorization header")
                
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() != "bearer":
                raise AuthError("Invalid authentication scheme")
                
            # Verify token
            payload = await self.verify_jwt(token)
            return payload
            
        except Exception as e:
            raise AuthError(f"Authentication failed: {str(e)}")
