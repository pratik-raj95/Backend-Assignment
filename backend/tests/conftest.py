import asyncio
import os
import tempfile
import pytest
import numpy as np
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient

import sys
# Set testing environment variables before importing settings
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

# Ensure backend folder is in Python path for import resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.main import app

from app.db.database import get_db, Base
from app.core.config import settings
# RedisCache import removed
from app.services.embedding_service import EmbeddingService
from app.utils.faiss_manager import FAISSIndexManager

# 1. Setup temporary path for FAISS testing
temp_index_dir = tempfile.mkdtemp()
temp_index_file = os.path.join(temp_index_dir, "test_faiss_index.bin")
settings.FAISS_INDEX_PATH = temp_index_file

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Cleans up any testing files created during run.
    """
    yield
    # Cleanup temp faiss binary
    if os.path.exists(temp_index_file):
        try:
            os.remove(temp_index_file)
            os.rmdir(temp_index_dir)
        except Exception:
            pass

# 2. Async database fixtures
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False}
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates tables, yields a session, and drops tables after test completion.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with TestSessionLocal() as session:
        yield session
        await session.close()
        
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# 3. Override FastAPI database dependency
@pytest.fixture(scope="function", autouse=True)
def override_db_dependency(db_session: AsyncSession):
    async def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

# 4. Mock EmbeddingService to return static test vectors
@pytest.fixture(scope="function", autouse=True)
def mock_embedding_service(monkeypatch):
    def mock_generate_embedding(self, text: str) -> np.ndarray:
        # Return a deterministic unit vector based on the first character
        val = ord(text[0]) if text else 1.0
        vec = np.zeros(384, dtype=np.float32)
        vec[0] = val
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    monkeypatch.setattr(EmbeddingService, "generate_embedding", mock_generate_embedding)

# mock_redis_cache removed

# 6. Wipe and reset the FAISS Index before each test to ensure isolation
@pytest.fixture(scope="function", autouse=True)
def clear_faiss_index():
    faiss_manager = FAISSIndexManager()
    faiss_manager.clear()
    yield

# 7. Asynchronous HTTP Client for endpoints testing
@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
