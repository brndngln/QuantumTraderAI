from typing import Dict, Any, Optional, Type
import logging
import traceback
from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import json
from datetime import datetime
import aioredis

class ErrorDetails(BaseModel):
    timestamp: str
    error_type: str
    message: str
    request_path: str
    request_method: str
    request_headers: Dict[str, str]
    request_body: Optional[Dict]
    traceback: Optional[str]
    status_code: int

class ErrorHandler:
    def __init__(self, redis_url: str):
        self.logger = logging.getLogger(__name__)
        self.redis_pool = None
        self.initialize_redis(redis_url)
        self.error_threshold = 5  # Maximum errors before circuit breaker
        self.error_window = 60  # Time window in seconds
        self.error_count = 0
        self.last_error_time = datetime.now()
    
    async def initialize_redis(self, redis_url: str) -> None:
        """
        Initialize Redis connection
        """
        try:
            self.redis_pool = aioredis.from_url(redis_url, decode_responses=True)
            await self.redis_pool.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.error(f"Redis initialization failed: {str(e)}")
            raise
    
    async def handle_error(self, request: Request, exc: Exception) -> Response:
        """
        Handle and log errors
        """
        try:
            # Get request details
            request_body = await request.body()
            request_body = json.loads(request_body.decode()) if request_body else None
            
            # Create error details
            error_details = ErrorDetails(
                timestamp=datetime.now().isoformat(),
                error_type=type(exc).__name__,
                message=str(exc),
                request_path=str(request.url.path),
                request_method=request.method,
                request_headers=dict(request.headers),
                request_body=request_body,
                traceback=traceback.format_exc(),
                status_code=500
            )
            
            # Log error
            self.logger.error(
                f"Error in {request.method} {request.url.path}: {str(exc)}",
                extra={'error_details': error_details.dict()}
            )
            
            # Store in Redis
            await self.redis_pool.rpush(
                'error_logs',
                json.dumps(error_details.dict())
            )
            
            # Check circuit breaker
            self.error_count += 1
            if self.error_count >= self.error_threshold:
                time_since_last = (datetime.now() - self.last_error_time).total_seconds()
                if time_since_last < self.error_window:
                    self.logger.warning("Circuit breaker activated due to excessive errors")
                    raise CircuitBreakerException("Too many errors in short time period")
                self.error_count = 0
            self.last_error_time = datetime.now()
            
            # Return appropriate response
            if isinstance(exc, RequestValidationError):
                return Response(
                    content=json.dumps({
                        'error': 'Validation Error',
                        'details': exc.errors()
                    }),
                    status_code=422,
                    media_type="application/json"
                )
            
            return Response(
                content=json.dumps({
                    'error': 'Internal Server Error',
                    'message': str(exc)
                }),
                status_code=500,
                media_type="application/json"
            )
            
        except Exception as e:
            self.logger.error(f"Error in error handler: {str(e)}")
            return Response(
                content=json.dumps({
                    'error': 'Internal Server Error',
                    'message': 'An unexpected error occurred'
                }),
                status_code=500,
                media_type="application/json"
            )
    
    async def get_error_stats(self) -> Dict:
        """
        Get error statistics
        """
        try:
            # Get recent errors
            error_logs = await self.redis_pool.lrange('error_logs', -100, -1)
            errors = [json.loads(log) for log in error_logs]
            
            # Calculate statistics
            return {
                'total_errors': len(errors),
                'error_types': {
                    type(e['error_type']): e['message']
                    for e in errors
                },
                'most_common_errors': self._get_most_common_errors(errors),
                'error_rate': len(errors) / (datetime.now() - datetime.fromisoformat(errors[0]['timestamp'])).total_seconds() if errors else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting error stats: {str(e)}")
            return {'error': str(e)}
    
    def _get_most_common_errors(self, errors: List[Dict]) -> Dict:
        """
        Get most common error types
        """
        error_counts = {}
        for error in errors:
            error_type = error['error_type']
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return dict(sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5])  # Top 5 most common errors
    
    async def circuit_breaker(self, func: callable, *args, **kwargs) -> Any:
        """
        Circuit breaker pattern
        """
        try:
            return await func(*args, **kwargs)
            
        except Exception as e:
            self.error_count += 1
            if self.error_count >= self.error_threshold:
                time_since_last = (datetime.now() - self.last_error_time).total_seconds()
                if time_since_last < self.error_window:
                    raise CircuitBreakerException("Circuit breaker activated")
                self.error_count = 0
            self.last_error_time = datetime.now()
            raise e
