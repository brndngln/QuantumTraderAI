from typing import Dict, Any, Optional, Callable, Awaitable
import logging
import asyncio
import aioredis
from datetime import datetime, timedelta
from pydantic import BaseModel

class CircuitBreakerConfig(BaseModel):
    failure_threshold: int = 5
    reset_timeout: int = 60  # seconds
    window_size: int = 10  # seconds
    max_concurrent_requests: int = 100
    redis_url: str = "redis://localhost:6379"

class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.redis_pool = None
        self.initialize_redis()
        self.current_state = {}  # Store current state in memory for quick access
        self.cleanup_task = None
    
    async def initialize_redis(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_pool = aioredis.from_url(self.config.redis_url, decode_responses=True)
            await self.redis_pool.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.error(f"Redis initialization failed: {str(e)}")
            raise
    
    async def start_cleanup(self) -> None:
        """Start periodic cleanup of expired states"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup loop"""
        while True:
            try:
                # Clean up expired states
                keys = await self.redis_pool.keys("circuit:*")
                for key in keys:
                    state = await self.redis_pool.hgetall(key)
                    if not state:
                        continue
                        
                    last_update = datetime.fromisoformat(state.get('last_update', ''))
                    if datetime.now() - last_update > timedelta(seconds=self.config.window_size):
                        await self.redis_pool.delete(key)
                        if key in self.current_state:
                            del self.current_state[key]
                            
                await asyncio.sleep(self.config.window_size)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup loop failed: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def get_state(self, service_name: str, version: str = "latest") -> Dict:
        """Get circuit breaker state"""
        try:
            key = f"circuit:{service_name}:{version}"
            state = await self.redis_pool.hgetall(key)
            if not state:
                state = {
                    'state': 'closed',
                    'failures': 0,
                    'successes': 0,
                    'last_update': datetime.now().isoformat(),
                    'reset_time': None
                }
                await self.redis_pool.hset(key, mapping=state)
            
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to get state: {str(e)}")
            return {'error': str(e)}
    
    async def update_state(self, service_name: str, version: str, success: bool) -> None:
        """Update circuit breaker state"""
        try:
            key = f"circuit:{service_name}:{version}"
            state = await self.get_state(service_name, version)
            
            if success:
                state['successes'] += 1
                state['failures'] = 0
                state['state'] = 'closed'
                state['reset_time'] = None
            else:
                state['failures'] += 1
                state['successes'] = 0
                
                # Check if we should open the circuit
                if state['failures'] >= self.config.failure_threshold:
                    state['state'] = 'open'
                    state['reset_time'] = (datetime.now() + timedelta(seconds=self.config.reset_timeout)).isoformat()
                    
            state['last_update'] = datetime.now().isoformat()
            await self.redis_pool.hset(key, mapping=state)
            self.current_state[key] = state
            
        except Exception as e:
            self.logger.error(f"Failed to update state: {str(e)}")
            raise
    
    async def is_circuit_open(self, service_name: str, version: str) -> bool:
        """Check if circuit is open"""
        try:
            key = f"circuit:{service_name}:{version}"
            state = await self.get_state(service_name, version)
            
            if state['state'] == 'open':
                if state['reset_time']:
                    reset_time = datetime.fromisoformat(state['reset_time'])
                    if datetime.now() > reset_time:
                        # Move to half-open state
                        state['state'] = 'half_open'
                        state['failures'] = 0
                        state['successes'] = 0
                        await self.redis_pool.hset(key, mapping=state)
                        self.current_state[key] = state
                        return False
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check circuit state: {str(e)}")
            return True  # Default to open on error
    
    async def execute_with_circuit_breaker(
        self,
        service_name: str,
        version: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with circuit breaker"""
        try:
            # Check if circuit is open
            if await self.is_circuit_open(service_name, version):
                raise CircuitBreakerException("Circuit is open")
                
            # Execute function
            result = await func(*args, **kwargs)
            
            # Update success
            await self.update_state(service_name, version, True)
            return result
            
        except Exception as e:
            # Update failure
            await self.update_state(service_name, version, False)
            raise
    
    async def get_metrics(self, service_name: str, version: str = "latest") -> Dict:
        """Get circuit breaker metrics"""
        try:
            key = f"circuit:{service_name}:{version}"
            state = await self.redis_pool.hgetall(key)
            if not state:
                return {'error': 'Service not found'}
                
            metrics = {
                'service': service_name,
                'version': version,
                'state': state.get('state', 'unknown'),
                'failures': int(state.get('failures', 0)),
                'successes': int(state.get('successes', 0)),
                'last_update': state.get('last_update', ''),
                'reset_time': state.get('reset_time', None),
                'threshold': self.config.failure_threshold,
                'reset_timeout': self.config.reset_timeout,
                'window_size': self.config.window_size
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics: {str(e)}")
            return {'error': str(e)}
    
    async def reset_circuit(self, service_name: str, version: str = "latest") -> None:
        """Manually reset circuit breaker"""
        try:
            key = f"circuit:{service_name}:{version}"
            state = {
                'state': 'closed',
                'failures': 0,
                'successes': 0,
                'last_update': datetime.now().isoformat(),
                'reset_time': None
            }
            await self.redis_pool.hset(key, mapping=state)
            if key in self.current_state:
                self.current_state[key] = state
            
        except Exception as e:
            self.logger.error(f"Failed to reset circuit: {str(e)}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown circuit breaker"""
        try:
            if self.cleanup_task:
                self.cleanup_task.cancel()
            if self.redis_pool:
                await self.redis_pool.close()
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")

class CircuitBreakerException(Exception):
    """Circuit breaker exception"""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
