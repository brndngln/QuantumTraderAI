import logging
from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.sessions import SessionMiddleware
from fastapi.middleware.authentication import AuthenticationMiddleware
from sentry_sdk import init, capture_exception
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.gzip import GZipMiddleware as StarletteGZipMiddleware
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
from starlette.middleware.sessions import SessionMiddleware as StarletteSessionMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware as StarletteAuthMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware as StarletteTrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware as StarletteHTTPSRedirectMiddleware
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
import uvicorn
import logging
from datetime import datetime
import traceback
import time
import asyncio
from typing import Dict, Any, Optional, List, Union
import json
import hashlib
import hmac
import secrets
from pydantic import BaseModel, Field, validator
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext
import aiohttp
import aioredis
from cachetools import TTLCache
import psutil
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import numpy as np
import numba
from numba import jit, prange
import pandas as pd
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
import boto3
from botocore.config import Config
import google.cloud.storage as gcs
from google.oauth2 import service_account
import redis
from redis import asyncio as aioredis
from redis.exceptions import ConnectionError
import memcache
from memcache import Client
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.dataset as ds
from pyarrow.lib import ArrowException
import httpx
from httpx import AsyncClient
import uvloop
import trio
import anyio
from anyio import create_task_group
from hypercorn import Config as HypercornConfig
from uvicorn import Config as UvicornConfig
from gunicorn.app.base import BaseApplication
import uvloop
import trio
import anyio
from anyio import create_task_group
from hypercorn import Config as HypercornConfig
from uvicorn import Config as UvicornConfig
from gunicorn.app.base import BaseApplication
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.pool import Pool
from sqlalchemy import event

# AI Safety Configuration
AI_CONFIG = {
    'max_strategy_weight': 0.5,  # Maximum weight any single strategy can have
    'min_strategy_weight': 0.1,  # Minimum weight any strategy can have
    'max_position_size': 0.1,    # Maximum position size as % of portfolio
    'require_user_confirmation': True,  # Require user confirmation for AI decisions
    'log_level': 'DEBUG',        # Detailed logging of AI activities
    'max_consecutive_losses': 3, # Maximum consecutive losses before AI pause
    'max_drawdown': 0.05        # Maximum allowed drawdown before AI pause
}

# Initialize AI safety monitoring
ai_safety_monitor = {
    'consecutive_losses': 0,
    'current_drawdown': 0,
    'last_user_confirmation': None,
    'active': True,
    'last_decision': None
}

# AI decision logging
async def log_ai_decision(decision_type: str, details: dict):
    """Log AI decisions with full context"""
    logger.info({
        'type': 'AI_DECISION',
        'timestamp': datetime.now().isoformat(),
        'decision_type': decision_type,
        'details': details,
        'user_override': False
    })

# AI safety check
async def check_ai_safety(trade_details: dict) -> bool:
    """Check if AI decision is within safety parameters"""
    if not ai_safety_monitor['active']:
        return False
        
    if trade_details['position_size'] > AI_CONFIG['max_position_size']:
        return False
        
    if ai_safety_monitor['consecutive_losses'] >= AI_CONFIG['max_consecutive_losses']:
        return False
        
    if ai_safety_monitor['current_drawdown'] >= AI_CONFIG['max_drawdown']:
        return False
        
    return True

# User confirmation required
async def require_user_confirmation(decision: dict) -> bool:
    """Require user confirmation for AI decisions"""
    if not AI_CONFIG['require_user_confirmation']:
        return True
        
    # Add user confirmation logic here
    return False  # Placeholder for actual implementation

# Initialize logging with enhanced configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(process)d - %(threadName)s',
    handlers=[
        logging.FileHandler('quantum_trader.log', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S.%f'
)
logger = logging.getLogger("quantum_trader")

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name='localhost',
    agent_port=6831,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Database configuration
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/quantum_trader"
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)

Base = declarative_base()

# Database models
class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    quantity = Column(Float)
    price = Column(Float)
    side = Column(String)
    timestamp = Column(DateTime)
    strategy = Column(String)
    status = Column(String)
    
    __table_args__ = (
        Index('idx_trades_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_trades_strategy', 'strategy'),
        Index('idx_trades_status', 'status')
    )

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy = Column(String, index=True)
    metric_name = Column(String, index=True)
    value = Column(Float)
    timestamp = Column(DateTime)
    
    __table_args__ = (
        Index('idx_metrics_strategy_timestamp', 'strategy', 'timestamp'),
        Index('idx_metrics_name', 'metric_name')
    )

class RiskMetric(Base):
    __tablename__ = "risk_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    metric_name = Column(String, index=True)
    value = Column(Float)
    timestamp = Column(DateTime)
    
    __table_args__ = (
        Index('idx_risk_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_risk_name', 'metric_name')
    )

# Database connection pool management
@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        raise exc.DisconnectionError()
    cursor.close()

# Database session dependency
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

# Cache configuration
CACHE_CONFIG = {
    'default': {
        'cache': 'aiocache.RedisCache',
        'endpoint': 'localhost',
        'port': 6379,
        'ttl': 300,
        'timeout': 1
    },
    'market_data': {
        'cache': 'aiocache.RedisCache',
        'endpoint': 'localhost',
        'port': 6379,
        'ttl': 60,
        'timeout': 0.5
    },
    'performance': {
        'cache': 'aiocache.RedisCache',
        'endpoint': 'localhost',
        'port': 6379,
        'ttl': 3600,
        'timeout': 1
    }
}

# Initialize cache
async def get_cache(namespace='default'):
    config = CACHE_CONFIG[namespace]
    cache = await aiocache.Cache.create(**config)
    return cache

# Initialize app with enhanced security
app = FastAPI(
    title="Quantum Trader AI API",
    description="Advanced trading platform with AI-powered strategies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
    default_response_class=JSONResponse
)

# Initialize OpenTelemetry instrumentation
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()
SQLAlchemyInstrumentor().instrument(engine=engine)

# Rate limiter configuration
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_REQUESTS = 100
rate_limit_cache = TTLCache(maxsize=1000, ttl=RATE_LIMIT_WINDOW)

# JWT configuration
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize Redis
redis_pool = None

async def get_redis_pool():
    global redis_pool
    if redis_pool is None:
        redis_pool = await aioredis.create_redis_pool('redis://localhost')
    return redis_pool

# Initialize Memcached
memcached_client = None

async def get_memcached_client():
    global memcached_client
    if memcached_client is None:
        memcached_client = Client(['localhost:11211'])
    return memcached_client

# Initialize Sentry with enhanced configuration
init(
    dsn="your_sentry_dsn_here",
    traces_sample_rate=1.0,
    environment="production",
    integrations=[
        FastAPIIntegration(transaction_style="url"),
        RedisIntegration(),
        AiohttpIntegration()
    ],
    before_send=lambda event, hint: {
        **event,
        "user": {
            "id": "user_id",
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0"
        },
        "context": {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent
        }
    }
)

# Security configurations
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redis connection pool
redis_pool = None

async def get_redis_pool():
    global redis_pool
    if redis_pool is None:
        redis_pool = await aioredis.create_redis_pool('redis://localhost')
    return redis_pool

# Rate limiting
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_REQUESTS = 100
rate_limit_cache = TTLCache(maxsize=1000, ttl=RATE_LIMIT_WINDOW)

# Request validation
class RequestValidator:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def validate_request(self, request: Request):
        # Validate IP
        if not await self._validate_ip(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP not allowed"
            )
            
        # Validate rate limit
        if not await self._validate_rate_limit(request):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
            
        # Validate headers
        if not await self._validate_headers(request):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid headers"
            )
            
        return True
        
    async def _validate_ip(self, request: Request):
        ip = request.client.host
        allowed_ips = ['127.0.0.1', 'localhost']
        return ip in allowed_ips
        
    async def _validate_rate_limit(self, request: Request):
        client_id = request.client.host
        if client_id not in rate_limit_cache:
            rate_limit_cache[client_id] = 0
        
        rate_limit_cache[client_id] += 1
        return rate_limit_cache[client_id] <= RATE_LIMIT_REQUESTS
        
    async def _validate_headers(self, request: Request):
        headers = request.headers
        required_headers = ['accept', 'user-agent']
        return all(header in headers for header in required_headers)

# Custom error handler with enhanced functionality
@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    # Log detailed error information
    logger.error(
        f"Unhandled exception: {str(exc)}\n"
        f"Traceback: {traceback.format_exc()}\n"
        f"Request: {request.method} {request.url}\n"
        f"Headers: {dict(request.headers)}\n"
        f"Client IP: {request.client.host}\n"
        f"Timestamp: {datetime.now().isoformat()}"
    )
    
    # Send to Sentry with enhanced context
    capture_exception(exc, {
        "extra": {
            "request_data": {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers)
            },
            "client_info": {
                "ip": request.client.host,
                "timestamp": datetime.now().isoformat()
            }
        }
    })
    
    # Return appropriate response
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Request failed",
                "detail": exc.detail,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

# Security middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Performance monitoring middleware
@app.middleware("http")
async def monitor_performance(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log slow requests
    if process_time > 1.0:  # 1 second threshold
        logger.warning(
            f"Slow request: {request.url.path} took {process_time:.2f}s\n"
            f"Headers: {dict(request.headers)}\n"
            f"Client IP: {request.client.host}"
        )
    
    # Update metrics
    await update_metrics(request.url.path, process_time)
    return response

# Metrics tracking
async def update_metrics(endpoint: str, response_time: float):
    pool = await get_redis_pool()
    await pool.incr(f"metrics:endpoint:{endpoint}:count")
    await pool.zadd(f"metrics:endpoint:{endpoint}:times", {
        str(time.time()): response_time
    })
    
# Circuit breaker
CIRCUIT_TIMEOUT = 30000  # 30 seconds
last_failure_time = 0
circuit_open = False

async def circuit_breaker(fn, *args, **kwargs):
    global circuit_open, last_failure_time
    
    if circuit_open:
        current_time = time.time()
        if current_time - last_failure_time < CIRCUIT_TIMEOUT:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable due to high error rate"
            )
        circuit_open = False
    
    try:
        return await fn(*args, **kwargs)
    except Exception as e:
        last_failure_time = time.time()
        circuit_open = True
        raise

# Background task management
background_tasks = set()

async def run_background_task(task):
    try:
        await task
    except Exception as e:
        logger.error(f"Background task failed: {str(e)}")
        capture_exception(e)
    finally:
        background_tasks.discard(task)

# Cache management
class CacheManager:
    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes
        self.lock = asyncio.Lock()
        
    async def get(self, key: str):
        async with self.lock:
            return self.cache.get(key)
            
    async def set(self, key: str, value: Any):
        async with self.lock:
            self.cache[key] = value
            
    async def invalidate(self, key: str):
        async with self.lock:
            if key in self.cache:
                del self.cache[key]

cache_manager = CacheManager()

# Request validation middleware
@app.middleware("http")
async def validate_request(request: Request, call_next):
    validator = RequestValidator()
    if await validator.validate_request(request):
        return await call_next(request)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Request validation failed"
    )

# Rate limiter middleware
class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
        
    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host
        
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Remove old requests
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if time.time() - t < self.window_seconds
        ]
        
        if len(self.requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        self.requests[client_ip].append(time.time())
        return await call_next(request)

# Performance monitoring middleware
class PerformanceMonitor:
    def __init__(self):
        self.requests = []
        
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        self.requests.append({
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "process_time": process_time,
            "timestamp": datetime.now().isoformat()
        })
        
        # Log slow requests
        if process_time > 1.0:  # 1 second threshold
            logger.warning(f"Slow request: {request.url.path} took {process_time:.2f}s")
        
        return response

# Initialize app with enhanced security
app = FastAPI(
    title="Quantum Trader AI API",
    description="Advanced trading platform with AI-powered strategies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
    default_response_class=JSONResponse
)

# Enhanced middleware stack
app.add_middleware(
    StarletteCORSMiddleware,
    allow_origins=["http://localhost:3000", "https://quantumtrader.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-Rate-Limit-Limit", "X-Rate-Limit-Remaining", "X-Cache-Hit", "X-Cache-Miss"],
    allow_origin_regex="^https?://(localhost:\d+|quantumtrader\.ai)$",
    max_age=3600
)

app.add_middleware(
    StarletteGZipMiddleware,
    minimum_size=1000,
    compresslevel=9,
    server_side=True,
    client_side=True
)

app.add_middleware(
    StarletteTrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "quantumtrader.ai", "*.quantumtrader.ai"],
    except_hosts=["localhost", "127.0.0.1"]
)

app.add_middleware(
    StarletteHTTPSRedirectMiddleware,
    status_code=status.HTTP_308_PERMANENT_REDIRECT,
    ssl_host="quantumtrader.ai",
    ssl_port=443
)

app.add_middleware(
    StarletteSessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    session_cookie="quantum_trader_session",
    same_site="lax",
    https_only=True,
    cookie_domain="quantumtrader.ai"
)

# Add additional security middleware
app.add_middleware(
    SecurityHeadersMiddleware,
    headers={
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';",
        "X-Permitted-Cross-Domain-Policies": "none",
        "X-Download-Options": "noopen",
        "X-Content-Type-Options": "nosniff"
    }
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    max_requests=RATE_LIMIT_REQUESTS,
    window=RATE_LIMIT_WINDOW,
    key_func=lambda request: request.client.host,
    storage=RedisRateLimitStorage(redis_pool),
    on_limit_exceeded=lambda request: JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "retry_after": RATE_LIMIT_WINDOW
        }
    )
)

# Add performance monitoring middleware
app.add_middleware(
    PerformanceMonitorMiddleware,
    threshold=1.0,  # 1 second
    metrics_store=RedisMetricsStore(redis_pool),
    on_slow_request=lambda request, response: {
        "endpoint": request.url.path,
        "duration": response.headers.get("X-Process-Time"),
        "status_code": response.status_code,
        "timestamp": datetime.now().isoformat()
    }
)

# Add error handling middleware
app.add_middleware(
    ErrorHandlerMiddleware,
    handlers={
        HTTPException: lambda request, exc: JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Request failed",
                "detail": exc.detail,
                "timestamp": datetime.now().isoformat()
            }
        ),
        SQLAlchemyError: lambda request, exc: JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Database error",
                "detail": str(exc),
                "timestamp": datetime.now().isoformat()
            }
        ),
        RedisConnectionError: lambda request, exc: JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Cache service unavailable",
                "detail": str(exc),
                "timestamp": datetime.now().isoformat()
            }
        )
    }
)

# Add authentication middleware
app.add_middleware(
    AuthenticationMiddleware,
    backend=JWTAuthenticationBackend(
        secret_key=SECRET_KEY,
        algorithm=ALGORITHM,
        token_expiration=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        token_issuer="quantumtrader.ai",
        token_audience="quantumtrader.ai"
    ),
    on_error=lambda request, exc: JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "Unauthorized",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )
)

# Add caching middleware
app.add_middleware(
    CacheMiddleware,
    cache=cache_manager,
    cache_key_func=lambda request: f"{request.method}:{request.url.path}:{request.headers.get('Authorization', '')}",
    cache_ttl=300,
    cache_bypass_func=lambda request: request.headers.get('X-No-Cache') == 'true'
)

# Add tracing middleware
app.add_middleware(
    TracingMiddleware,
    tracer=trace.get_tracer(__name__),
    span_name_func=lambda request: f"{request.method} {request.url.path}",
    trace_id_header="X-Trace-ID",
    span_id_header="X-Span-ID"
)

# Add logging middleware
app.add_middleware(
    LoggingMiddleware,
    logger=logger,
    log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_level=logging.INFO,
    include_headers=True,
    include_body=True
)

# Add request validation middleware
app.add_middleware(
    RequestValidationMiddleware,
    validators=[
        IPValidator(allowed_ips=['127.0.0.1', 'localhost', 'quantumtrader.ai']),
        HeaderValidator(required_headers=['accept', 'user-agent']),
        RateLimitValidator(max_requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
    ]
)

# Add circuit breaker middleware
app.add_middleware(
    CircuitBreakerMiddleware,
    failure_threshold=5,
    reset_timeout=60,
    on_circuit_open=lambda request: JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Service temporarily unavailable due to high error rate",
            "timestamp": datetime.now().isoformat()
        }
    )
)

# Cache for market data
market_data_cache = {}
last_cache_update = datetime.min
CACHE_TTL = 300  # 5 minutes

# Circuit breaker
CIRCUIT_TIMEOUT = 30000  # 30 seconds
last_failure_time = 0
circuit_open = False

async def circuit_breaker(fn, *args, **kwargs):
    global circuit_open, last_failure_time
    
    if circuit_open:
        current_time = time.time()
        if current_time - last_failure_time < CIRCUIT_TIMEOUT:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable due to high error rate"
            )
        circuit_open = False
    
    try:
        return await fn(*args, **kwargs)
    except Exception as e:
        last_failure_time = time.time()
        circuit_open = True
        raise

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_load": {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent
        }
    }

@app.get("/metrics", status_code=status.HTTP_200_OK)
async def get_metrics():
    return {
        "cache": {
            "size": len(market_data_cache),
            "last_update": last_cache_update.isoformat()
        },
        "performance": {
            "requests": len(performance_monitor.requests),
            "slow_requests": len([r for r in performance_monitor.requests if r["process_time"] > 1.0])
        },
        "circuit_breaker": {
            "status": "open" if circuit_open else "closed",
            "last_failure": last_failure_time
        }
    }

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {
        "status": "QuantumTraderAI is live",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/run")
def run_all_strategies():
    try:
        logger.info("Starting strategy execution")
        
        # Load data with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                data = load_realtime_data()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    capture_exception(e)  # Send to Sentry
                    raise
                logger.warning(f"Data load attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff

        # Execute strategies with error handling
        try:
            momentum_signals = momentum_strategy(data)
            mean_reversion_signals = mean_reversion_strategy(data)
            
            # Validate trade signals
            if not isinstance(momentum_signals, list) or not isinstance(mean_reversion_signals, list):
                raise ValueError("Strategy signals must be lists")
                
            trades = execute_trade(momentum_signals + mean_reversion_signals)
            logger.info(f"Successfully executed {len(trades)} trades")
            
            return {
                "status": "success",
                "trades_executed": trades,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Strategy execution failed: {str(e)}")
            capture_exception(e)  # Send to Sentry
            raise HTTPException(status_code=500, detail=str(e))
            
    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        capture_exception(e)  # Send to Sentry
        raise HTTPException(status_code=500, detail=error_msg)
