from typing import List
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.repository.user_repository import UserRepository
from app.repository.event_repository import EventRepository
from app.services.similarity_service import SimilarityService
from app.schemas.similarity import SimilarUserDetail
from app.core.exceptions import ValidationException
from app.core.limiter import limiter

router = APIRouter()

@router.get(
    "/similar-users", 
    response_model=List[SimilarUserDetail],
    status_code=status.HTTP_200_OK
)
@limiter.limit("30/minute")
async def get_similar_users(
    request: Request,
    userId: str = Query(..., alias="userId", min_length=1, description="Target User ID to find matches for"),
    limit: int = Query(5, ge=1, le=20, description="Max count of similar users to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Computes profile-based behavioral similarities between users.
    Determines cosine similarity of behavioral centroids compiled from vector index histories.
    """
    if not userId.strip():
        raise ValidationException("userId parameter must contain at least one non-whitespace character.")

    # Instantiate repositories and services
    user_repo = UserRepository(db)
    event_repo = EventRepository(db)
    similarity_service = SimilarityService(user_repo, event_repo)

    similar_users = await similarity_service.get_similar_users(
        target_user_id=userId,
        limit=limit
    )

    return [
        SimilarUserDetail(
            userId=user["userId"],
            similarity_score=user["similarity_score"],
            total_events=user["total_events"],
            last_active=user["last_active"]
        )
        for user in similar_users
    ]
