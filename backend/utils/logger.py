import logging
import logging.handlers
import os
import sys
from datetime import datetime
import json
from typing import Dict, Any, Optional
import asyncio
import aioredis

class CustomFormatter(logging.Formatter):
    """Custom log formatter with structured output"""
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'service': 'quantum_trader',
            'component': record.name,
            'message': record.getMessage(),
            'trace_id': getattr(record, 'trace_id', None),
            'user_id': getattr(record, 'user_id', None),
            'request_id': getattr(record, 'request_id', None),
            'extra': getattr(record, 'extra', {})
        }
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

class AsyncRedisHandler(logging.Handler):
    """Async Redis log handler"""
    def __init__(self, redis_url: str, channel: str = 'logs'):
        super().__init__()
        self.redis_url = redis_url
        self.channel = channel
        self.redis_pool = None
        self.initialize_redis()
    
    async def initialize_redis(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_pool = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis_pool.ping()
        except Exception as e:
            print(f"Redis initialization failed: {str(e)}")
    
    async def emit(self, record: logging.LogRecord) -> None:
        """Emit log record to Redis"""
        try:
            if not self.redis_pool:
                await self.initialize_redis()
                
            log_entry = self.format(record)
            await self.redis_pool.rpush(self.channel, log_entry)
            
        except Exception as e:
            print(f"Error emitting log to Redis: {str(e)}")

class Logger:
    def __init__(self, name: str, redis_url: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.redis_url = redis_url
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        # Remove existing handlers
        self.logger.handlers = []
        
        # Set log level
        self.logger.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(CustomFormatter())
        self.logger.addHandler(console_handler)
        
        # Create file handler
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'quantum_trader.log'),
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(CustomFormatter())
        self.logger.addHandler(file_handler)
        
        # Create Redis handler if configured
        if self.redis_url:
            redis_handler = AsyncRedisHandler(self.redis_url)
            redis_handler.setLevel(logging.INFO)
            redis_handler.setFormatter(CustomFormatter())
            self.logger.addHandler(redis_handler)
    
    def with_context(self, **kwargs) -> 'Logger':
        """Add context to logger"""
        return ContextLogger(self.logger, **kwargs)
    
    def get_logger(self) -> logging.Logger:
        """Get the underlying logger"""
        return self.logger

class ContextLogger(Logger):
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.context = kwargs
    
    def _add_context(self, record: logging.LogRecord) -> None:
        """Add context to log record"""
        for key, value in self.context.items():
            setattr(record, key, value)
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Debug level log with context"""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.DEBUG,
            self.logger.findCaller(),
            0,
            msg,
            args,
            None,
            **kwargs
        )
        self._add_context(record)
        self.logger.handle(record)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Info level log with context"""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            self.logger.findCaller(),
            0,
            msg,
            args,
            None,
            **kwargs
        )
        self._add_context(record)
        self.logger.handle(record)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Warning level log with context"""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.WARNING,
            self.logger.findCaller(),
            0,
            msg,
            args,
            None,
            **kwargs
        )
        self._add_context(record)
        self.logger.handle(record)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """Error level log with context"""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.ERROR,
            self.logger.findCaller(),
            0,
            msg,
            args,
            None,
            **kwargs
        )
        self._add_context(record)
        self.logger.handle(record)
    
    def exception(self, msg: str, *args, **kwargs) -> None:
        """Exception level log with context"""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.ERROR,
            self.logger.findCaller(),
            0,
            msg,
            args,
            sys.exc_info(),
            **kwargs
        )
        self._add_context(record)
        self.logger.handle(record)

def get_logger(name: str, redis_url: Optional[str] = None) -> Logger:
    """Get or create a logger instance"""
    return Logger(name, redis_url)
