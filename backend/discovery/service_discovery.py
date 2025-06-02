from typing import Dict, Any, Optional, List, Tuple
import logging
import asyncio
import aioredis
import json
from datetime import datetime, timedelta
from pydantic import BaseModel
import socket

class ServiceConfig(BaseModel):
    name: str
    version: str
    host: str
    port: int
    health_check_path: str = "/health"
    weight: int = 100
    max_failures: int = 3
    failure_window: int = 60  # seconds
    tags: List[str] = []

class ServiceDiscovery:
    def __init__(self, redis_url: str):
        self.logger = logging.getLogger(__name__)
        self.redis_pool = None
        self.initialize_redis(redis_url)
        self.failure_threshold = 0.5  # 50% failure rate
        self.health_check_interval = 10  # seconds
        self.health_check_task = None
        self.services = {}
    
    async def initialize_redis(self, redis_url: str) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_pool = aioredis.from_url(redis_url, decode_responses=True)
            await self.redis_pool.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.error(f"Redis initialization failed: {str(e)}")
            raise
    
    async def register_service(self, config: ServiceConfig) -> None:
        """Register a new service"""
        try:
            service_key = f"service:{config.name}:{config.version}"
            service_data = {
                'host': config.host,
                'port': config.port,
                'weight': config.weight,
                'tags': config.tags,
                'last_updated': datetime.now().isoformat(),
                'status': 'healthy',
                'failures': 0,
                'last_failure': None
            }
            
            await self.redis_pool.hset(service_key, mapping=service_data)
            self.logger.info(f"Registered service: {config.name}:{config.version}")
            
            # Start health checking
            self.start_health_checking()
            
        except Exception as e:
            self.logger.error(f"Service registration failed: {str(e)}")
            raise
    
    async def deregister_service(self, service_name: str, version: str) -> None:
        """Deregister a service"""
        try:
            service_key = f"service:{service_name}:{version}"
            await self.redis_pool.delete(service_key)
            self.logger.info(f"Deregistered service: {service_name}:{version}")
            
        except Exception as e:
            self.logger.error(f"Service deregistration failed: {str(e)}")
            raise
    
    async def get_service(self, service_name: str, version: str = "latest") -> Optional[Dict]:
        """Get service information"""
        try:
            if version == "latest":
                # Get all versions and return the latest
                keys = await self.redis_pool.keys(f"service:{service_name}:*")
                if not keys:
                    return None
                    
                latest_key = max(keys, key=lambda k: k.split(':')[-1])
                return await self.redis_pool.hgetall(latest_key)
                
            service_key = f"service:{service_name}:{version}"
            return await self.redis_pool.hgetall(service_key)
            
        except Exception as e:
            self.logger.error(f"Failed to get service: {str(e)}")
            return None
    
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
    
    async def health_check(self, service_key: str) -> bool:
        """Perform health check on service"""
        try:
            service = await self.redis_pool.hgetall(service_key)
            if not service:
                return False
                
            host = service['host']
            port = int(service['port'])
            
            # Create connection
            conn = socket.create_connection((host, port), timeout=5)
            conn.close()
            
            # Update health status
            await self.redis_pool.hset(service_key, 'status', 'healthy')
            await self.redis_pool.hset(service_key, 'failures', 0)
            await self.redis_pool.hset(service_key, 'last_updated', datetime.now().isoformat())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed for {service_key}: {str(e)}")
            return False
    
    async def update_service_status(self, service_key: str, healthy: bool) -> None:
        """Update service status based on health check"""
        try:
            service = await self.redis_pool.hgetall(service_key)
            if not service:
                return
                
            failures = int(service.get('failures', 0))
            last_failure = service.get('last_failure')
            
            if not healthy:
                failures += 1
                await self.redis_pool.hset(service_key, 'failures', failures)
                await self.redis_pool.hset(service_key, 'last_failure', datetime.now().isoformat())
                
                # Check if service should be marked as unhealthy
                if failures >= int(service.get('max_failures', 3)):
                    await self.redis_pool.hset(service_key, 'status', 'unhealthy')
                    self.logger.warning(f"Service {service_key} marked as unhealthy")
                    
            else:
                await self.redis_pool.hset(service_key, 'failures', 0)
                await self.redis_pool.hset(service_key, 'status', 'healthy')
                
        except Exception as e:
            self.logger.error(f"Failed to update service status: {str(e)}")
    
    async def start_health_checking(self) -> None:
        """Start periodic health checking"""
        if self.health_check_task:
            self.health_check_task.cancel()
            
        self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self) -> None:
        """Periodic health check loop"""
        while True:
            try:
                keys = await self.redis_pool.keys("service:*")
                for key in keys:
                    healthy = await self.health_check(key)
                    await self.update_service_status(key, healthy)
                    
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check loop failed: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
    
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
    
    async def get_service_status(self, service_name: str) -> Dict:
        """Get service status and health metrics"""
        try:
            keys = await self.redis_pool.keys(f"service:{service_name}:*")
            status = {
                'name': service_name,
                'total_instances': len(keys),
                'healthy_instances': 0,
                'unhealthy_instances': 0,
                'last_updated': datetime.now().isoformat(),
                'instances': []
            }
            
            for key in keys:
                service = await self.redis_pool.hgetall(key)
                if service:
                    status['instances'].append(service)
                    if service.get('status') == 'healthy':
                        status['healthy_instances'] += 1
                    else:
                        status['unhealthy_instances'] += 1
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get service status: {str(e)}")
            return {'error': str(e)}
    
    async def shutdown(self) -> None:
        """Shutdown service discovery"""
        try:
            if self.health_check_task:
                self.health_check_task.cancel()
            if self.redis_pool:
                await self.redis_pool.close()
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
