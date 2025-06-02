from typing import Dict, Any, Optional, List, Tuple
import logging
import asyncio
import aiohttp
import aioredis
import json
from datetime import datetime
from pydantic import BaseModel
from random import choice
import hashlib

class LoadBalancerConfig(BaseModel):
    strategy: str = "weighted_round_robin"  # round_robin, weighted_round_robin, random
    max_concurrent_requests: int = 100
    request_timeout: int = 5  # seconds
    health_check_interval: int = 10  # seconds
    redis_url: str = "redis://localhost:6379"

class LoadBalancer:
    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.redis_pool = None
        self.initialize_redis()
        self.current_index = {}  # For round-robin
        self.health_check_task = None
        self.session = None
    
    async def initialize_redis(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_pool = aioredis.from_url(self.config.redis_url, decode_responses=True)
            await self.redis_pool.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.error(f"Redis initialization failed: {str(e)}")
            raise
    
    async def initialize_session(self) -> None:
        """Initialize HTTP session"""
        try:
            self.session = aiohttp.ClientSession()
        except Exception as e:
            self.logger.error(f"HTTP session initialization failed: {str(e)}")
            raise
    
    async def start_health_checking(self) -> None:
        """Start periodic health checking"""
        if self.health_check_task:
            self.health_check_task.cancel()
            
        self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self) -> None:
        """Periodic health check loop"""
        while True:
            try:
                services = await self.get_all_services()
                for service in services:
                    await self.check_service_health(service)
                    
                await asyncio.sleep(self.config.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check loop failed: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def check_service_health(self, service: Dict) -> bool:
        """Check service health"""
        try:
            url = f"http://{service['host']}:{service['port']}{service.get('health_check_path', '/health')}"
            async with self.session.get(url, timeout=self.config.request_timeout) as response:
                if response.status == 200:
                    await self.redis_pool.hset(
                        f"service:{service['name']}:{service['version']}",
                        'status',
                        'healthy'
                    )
                    return True
                
            await self.redis_pool.hset(
                f"service:{service['name']}:{service['version']}",
                'status',
                'unhealthy'
            )
            return False
            
        except Exception as e:
            self.logger.error(f"Health check failed for service: {str(e)}")
            await self.redis_pool.hset(
                f"service:{service['name']}:{service['version']}",
                'status',
                'unhealthy'
            )
            return False
    
    async def get_all_services(self) -> List[Dict]:
        """Get all registered services"""
        try:
            keys = await self.redis_pool.keys("service:*")
            services = []
            for key in keys:
                service = await self.redis_pool.hgetall(key)
                if service:
                    services.append(service)
            return services
            
        except Exception as e:
            self.logger.error(f"Failed to get all services: {str(e)}")
            return []
    
    async def get_healthy_services(self, service_name: str) -> List[Dict]:
        """Get all healthy instances of a service"""
        try:
            keys = await self.redis_pool.keys(f"service:{service_name}:*")
            services = []
            for key in keys:
                service = await self.redis_pool.hgetall(key)
                if service and service.get('status') == 'healthy':
                    services.append(service)
            return services
            
        except Exception as e:
            self.logger.error(f"Failed to get healthy services: {str(e)}")
            return []
    
    def select_instance(self, service_name: str, service_version: str) -> Optional[Dict]:
        """Select instance based on load balancing strategy"""
        try:
            services = self.get_healthy_services(service_name)
            if not services:
                return None
                
            if self.config.strategy == "round_robin":
                return self._round_robin(services)
                
            elif self.config.strategy == "weighted_round_robin":
                return self._weighted_round_robin(services)
                
            elif self.config.strategy == "random":
                return self._random(services)
                
            return self._round_robin(services)  # Default to round-robin
            
        except Exception as e:
            self.logger.error(f"Instance selection failed: {str(e)}")
            return None
    
    def _round_robin(self, services: List[Dict]) -> Dict:
        """Round-robin selection"""
        if not services:
            return None
            
        key = f"{services[0]['name']}:{services[0]['version']}"
        if key not in self.current_index:
            self.current_index[key] = 0
            
        instance = services[self.current_index[key]]
        self.current_index[key] = (self.current_index[key] + 1) % len(services)
        return instance
    
    def _weighted_round_robin(self, services: List[Dict]) -> Dict:
        """Weighted round-robin selection"""
        if not services:
            return None
            
        # Get total weight
        total_weight = sum(int(s['weight']) for s in services)
        
        # Generate random number
        rand = int.from_bytes(os.urandom(4), byteorder="big") % total_weight
        
        # Find instance
        current_weight = 0
        for service in services:
            current_weight += int(service['weight'])
            if rand < current_weight:
                return service
        
        return services[0]  # Fallback to first service
    
    def _random(self, services: List[Dict]) -> Dict:
        """Random selection"""
        if not services:
            return None
            
        return choice(services)
    
    async def route_request(self, service_name: str, path: str, request: Dict) -> Tuple[Dict, int]:
        """Route request to appropriate service instance"""
        try:
            # Select instance
            instance = self.select_instance(service_name, "latest")
            if not instance:
                return ({"error": "No healthy instances available"}, 503)
                
            # Build URL
            url = f"http://{instance['host']}:{instance['port']}{path}"
            
            # Forward request
            async with self.session.request(
                request['method'],
                url,
                headers=request.get('headers', {}),
                data=request.get('body', None),
                timeout=self.config.request_timeout
            ) as response:
                content = await response.read()
                return ({
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body": content.decode()
                }, response.status)
                
        except Exception as e:
            self.logger.error(f"Request routing failed: {str(e)}")
            return ({"error": str(e)}, 500)
    
    async def get_load_stats(self) -> Dict:
        """Get load balancing statistics"""
        try:
            stats = {
                'total_services': 0,
                'healthy_services': 0,
                'unhealthy_services': 0,
                'distribution': {},
                'last_updated': datetime.now().isoformat()
            }
            
            services = await self.get_all_services()
            stats['total_services'] = len(services)
            
            for service in services:
                status = service.get('status', 'unknown')
                if status == 'healthy':
                    stats['healthy_services'] += 1
                else:
                    stats['unhealthy_services'] += 1
                    
                service_key = f"{service['name']}:{service['version']}"
                if service_key not in stats['distribution']:
                    stats['distribution'][service_key] = {
                        'status': status,
                        'requests': 0,
                        'failures': 0,
                        'last_updated': service.get('last_updated', '')
                    }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get load stats: {str(e)}")
            return {'error': str(e)}
    
    async def shutdown(self) -> None:
        """Shutdown load balancer"""
        try:
            if self.health_check_task:
                self.health_check_task.cancel()
            if self.session:
                await self.session.close()
            if self.redis_pool:
                await self.redis_pool.close()
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
