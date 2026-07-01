from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logger import logger, setup_logging
from app.core.limiter import limiter
from app.core.exceptions import InsightFlowException
from app.middleware.error_handler import TracingAndSizeLimitMiddleware, global_exception_handler
from app.api.api import api_router
from app.db.database import engine, SessionLocal, Base
from app.db import models
from app.utils.faiss_manager import FAISSIndexManager
from app.services.embedding_service import EmbeddingService
from app.api.routes.tracking import process_event_embedding_task

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App lifecycle manager. Performs logging, models initialization,
    and runs startup reconciliation on pending embeddings.
    """
    # 1. Setup Logging system
    setup_logging()
    logger.info("Initializing User Analytics Semantic Search System application lifecycle...")

    # 2. Initialize database tables
    try:
        logger.info("Creating database tables if they do not exist...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize database tables: {e}", exc_info=True)

    # 3. Start FAISS
    try:
        faiss_manager = FAISSIndexManager()
        logger.info(f"FAISS initialized. Total vectors: {faiss_manager.get_total_vectors()}")
    except Exception as e:
        logger.critical(f"Failed to load FAISS engine: {e}", exc_info=True)

    # 4. Load embedding model
    try:
        embedding_service = EmbeddingService()
        logger.info("Embedding service model loaded successfully.")
    except Exception as e:
        logger.critical(f"Failed to load embedding service model: {e}", exc_info=True)

    # 5. Check pending events
    logger.info("Checking for unprocessed pending event embeddings...")
    try:
        from app.repository.event_repository import EventRepository
        async with SessionLocal() as db_session:
            event_repo = EventRepository(db_session)
            pending_events = await event_repo.get_pending_events(limit=100)
            if pending_events:
                logger.info(f"Found {len(pending_events)} pending events needing embedding. Reconciling in background...")
                # Process sequentially on boot to prevent threading resource locks
                for event in pending_events:
                    await process_event_embedding_task(event.id)
            else:
                logger.info("Database reconciliation complete. No pending embeddings found.")
    except Exception as e:
        logger.error(f"Error during startup database reconciliation: {e}")

    yield

    # Shutdown actions
    logger.info("Shutting down User Analytics Semantic Search System application...")
    try:
        # Flush FAISS index
        faiss_manager = FAISSIndexManager()
        faiss_manager.save()
    except Exception as e:
        logger.error(f"Error saving FAISS state during shutdown: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None
)

# Wire rate limiting state and handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register custom global exception handlers
app.add_exception_handler(InsightFlowException, global_exception_handler)
app.add_exception_handler(RequestValidationError, global_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# CORS configuration
origins = settings.CORS_ORIGINS
if isinstance(origins, str):
    origins = [origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom tracing and size limiting middleware
app.add_middleware(
    TracingAndSizeLimitMiddleware,
    max_content_length=settings.REQUEST_MAX_SIZE_BYTES
)

# Include API v1 route prefix
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", include_in_schema=False)
async def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs" if settings.ENVIRONMENT == "development" else "hidden"
    }
