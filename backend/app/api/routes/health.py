import time
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.core.logger import logger

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Standard health check endpoint.
    Checks PostgreSQL connection health.
    """
    health_status = {
        "status": "healthy",
        "postgres": "unknown",
        "timestamp": time.time()
    }
    
    # 1. Test PostgreSQL
    try:
        start_time = time.time()
        await db.execute(text("SELECT 1"))
        postgres_latency = (time.time() - start_time) * 1000
        health_status["postgres"] = f"connected ({postgres_latency:.2f}ms)"
    except Exception as e:
        logger.error(f"Health check PostgreSQL connection failure: {e}")
        health_status["postgres"] = "disconnected"
        health_status["status"] = "unhealthy"

    if health_status["status"] == "unhealthy":
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status)

    return health_status
