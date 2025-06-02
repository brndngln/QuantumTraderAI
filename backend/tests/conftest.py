import pytest
import asyncio
import os
import json
import aioredis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from backend.api.main import app
from backend.database.models import Base
from backend.database.database import get_db
from backend.security.security_manager import SecurityManager
from backend.utils.logger import get_logger

# Create test database engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"  # In-memory SQLite for tests

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=AsyncSession
)

# Create test Redis client
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def redis_client():
    """Redis client fixture"""
    redis = await aioredis.from_url(TEST_REDIS_URL)
    yield redis
    redis.close()
    await redis.wait_closed()

@pytest.fixture(scope="session")
async def test_db():
    """Test database fixture"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield TestingSessionLocal()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="session")
def test_client():
    """Test client fixture"""
    client = TestClient(app)
    return client

@pytest.fixture(scope="session")
def security_manager():
    """Security manager fixture"""
    return SecurityManager()

@pytest.fixture(scope="session")
def logger():
    """Logger fixture"""
    return get_logger("test")

@pytest.fixture(scope="function")
async def db_session():
    """Database session fixture"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        await session.close()

@pytest.fixture(scope="function")
async def initialized_app():
    """Initialized FastAPI app fixture"""
    async with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
def mock_environment():
    """Mock environment variables fixture"""
    original_env = dict(os.environ)
    os.environ.update({
        "DATABASE_URL": TEST_DATABASE_URL,
        "REDIS_URL": TEST_REDIS_URL,
        "JWT_SECRET": "test-secret",
        "ENCRYPTION_KEY": "test-encryption-key"
    })
    yield
    os.environ.clear()
    os.environ.update(original_env)

# Override get_db dependency for tests
async def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        await db.close()

app.dependency_overrides[get_db] = override_get_db

# Helper functions
async def create_test_data(session: AsyncSession, data: Dict) -> None:
    """Create test data in database"""
    for model, items in data.items():
        for item in items:
            db_model = model(**item)
            session.add(db_model)
    await session.commit()

async def clear_test_data(session: AsyncSession) -> None:
    """Clear test data from database"""
    await session.execute("DELETE FROM trades")
    await session.execute("DELETE FROM models")
    await session.commit()
