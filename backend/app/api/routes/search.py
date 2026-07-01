from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.repository.event_repository import EventRepository
from app.services.search_service import SearchService
from app.schemas.search import SearchResponse
from app.core.exceptions import ValidationException
from app.core.limiter import limiter

router = APIRouter()

@router.get(
    "/search", 
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK
)
@limiter.limit("30/minute")
async def semantic_search(
    request: Request,
    query: str = Query(..., min_length=1, description="Text query to perform semantic similarity matching on"),
    limit: int = Query(10, ge=1, le=50, description="Maximum count of ranked items to return"),
    threshold: float = Query(0.0, ge=0.0, le=1.0, description="Minimum cosine similarity score threshold (0.0 to 1.0)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes a real-time semantic search vector match across tracked events using Sentence Transformers and FAISS.
    """
    if not query.strip():
        raise ValidationException("Query string parameter must contain at least one non-whitespace character.")

    # Instantiate repositories and services
    event_repo = EventRepository(db)
    search_service = SearchService(event_repo)

    results = await search_service.semantic_search(
        query=query,
        k=limit,
        threshold=threshold
    )

    return SearchResponse(results=results)
