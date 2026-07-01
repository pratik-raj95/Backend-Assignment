from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Create asynchronous engine for PostgreSQL connection pooling
# SQLite does not support pool_size or max_overflow
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False
}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs
)

# Async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    """
    Base declarative class for all SQLAlchemy 2.0 ORM models.
    """
    pass

async def get_db():
    """
    Dependency generator for injecting scoped asynchronous db sessions.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
