from typing import Dict, Any, Optional, Callable, Awaitable
import logging
import asyncio
import json
import aiohttp
from datetime import datetime
import aioredis
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from .auth import AuthService, AuthError
from .rate_limiter import RateLimiter

class GatewayConfig(BaseModel):
    services: Dict[str, Dict[str, Any]] = {
        "trading": {
            "url": "http://trading-service:8000",
            "rate_limit": 100,
            "timeout": 5
        },
        "ai": {
            "url": "http://ai-service:8000",
            "rate_limit": 50,
            "timeout": 10
        },
        "quantum": {
            "url": "http://quantum-service:8000",
            "rate_limit": 20,
            "timeout": 15
        }
    }
    redis_url: str = "redis://localhost:6379"
    auth_secret: str = "your-secret-key"
    max_concurrent_requests: int = 100

class APIGateway:
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.app = FastAPI(
            title="Quantum Trader API Gateway",
            description="API Gateway for Quantum Trader services",
            version="1.0.0"
        )
        self.redis_pool = None
        self.auth_service = None
        self.rate_limiter = None
        self.session = None
        self.initialize_components()
        self.setup_routes()
        self.setup_middlewares()
    
    def initialize_components(self) -> None:
        """Initialize components"""
        try:
            # Initialize Redis
            self.redis_pool = aioredis.from_url(self.config.redis_url, decode_responses=True)
            
            # Initialize auth service
            self.auth_service = AuthService(AuthConfig(
                jwt_secret=self.config.auth_secret,
                redis_url=self.config.redis_url
            ))
            
            # Initialize rate limiter
            self.rate_limiter = RateLimiter(self.config.redis_url)
            
            # Initialize HTTP session
            self.session = aiohttp.ClientSession()
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {str(e)}")
            raise
    
    def setup_middlewares(self) -> None:
        """Setup middlewares"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    def setup_routes(self) -> None:
        """Setup routes"""
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}
        
        @self.app.post("/{service}/{path:path}")
        async def proxy_request(
            service: str,
            path: str,
            request: Request,
            current_user: Dict = Depends(self.auth_service.get_current_user)
        ):
            try:
                # Rate limit
                await self.rate_limiter.rate_limit()(request)
                
                # Get service configuration
                service_config = self.config.services.get(service)
                if not service_config:
                    raise HTTPException(status_code=404, detail="Service not found")
                
                # Forward request
                url = f"{service_config['url']}/{path}"
                headers = dict(request.headers)
                headers["Authorization"] = f"Bearer {current_user['sub']}"
                
                async with self.session.request(
                    request.method,
                    url,
                    headers=headers,
                    data=await request.body()
                ) as response:
                    content = await response.read()
                    return Response(
                        content=content,
                        status_code=response.status,
                        headers=dict(response.headers)
                    )
                    
            except AuthError as e:
                raise HTTPException(status_code=e.status_code, detail=e.detail)
            except Exception as e:
                self.logger.error(f"Proxy request failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")
    
    async def get_service_status(self, service: str) -> Dict[str, Any]:
        """Get service status"""
        try:
            service_config = self.config.services.get(service)
            if not service_config:
                return {"status": "unknown", "service": service}
                
            async with self.session.get(f"{service_config['url']}/health") as response:
                if response.status == 200:
                    return {"status": "healthy", "service": service}
                return {"status": "unhealthy", "service": service}
                
        except Exception as e:
            self.logger.error(f"Failed to get service status: {str(e)}")
            return {"status": "unhealthy", "service": service}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        try:
            status = {
                "gateway": {"status": "healthy"},
                "services": {}
            }
            
            # Check each service
            for service in self.config.services:
                status["services"][service] = await self.get_service_status(service)
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get system status")
    
    async def shutdown(self) -> None:
        """Shutdown gateway"""
        try:
            if self.session:
                await self.session.close()
            if self.redis_pool:
                await self.redis_pool.close()
            
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
