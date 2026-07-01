import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.repository.event_repository import EventRepository
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import AnalyticsResponse
from app.core.exceptions import ValidationException
from app.core.limiter import limiter

router = APIRouter()

def parse_datetime(date_str: Optional[str]) -> Optional[datetime.datetime]:
    """
    Safely parses strings into timezone-aware datetime objects.
    Supports YYYY-MM-DD and full ISO-8601 formatting.
    """
    if not date_str:
        return None
    try:
        # Check if YYYY-MM-DD
        if len(date_str) == 10:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        else:
            dt = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        
        # Ensure timezone-aware (default UTC)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except ValueError as e:
        raise ValidationException(
            message=f"Failed to parse query date '{date_str}'. Use format 'YYYY-MM-DD' or ISO 8601 standard.",
            details=str(e)
        )

@router.get(
    "/analytics", 
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK
)
@limiter.limit("45/minute")
async def get_analytics(
    request: Request,
    event: Optional[str] = Query(None, description="Filter by exact event description name"),
    from_date: Optional[str] = Query(None, alias="from", description="Filter events starting at (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, alias="to", description="Filter events ending at (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves system analytical statistics including count totals, breakdown mapping,
    and highly active profiles. Rates are throttled to prevent script abuse.
    """
    # 1. Parse parameters
    parsed_from = parse_datetime(from_date)
    parsed_to = parse_datetime(to_date)

    if parsed_from and parsed_to and parsed_from > parsed_to:
        raise ValidationException("Range bounds error: 'from' timestamp must be chronologically before 'to' timestamp.")

    # 2. Query Analytics Service
    event_repo = EventRepository(db)
    analytics_service = AnalyticsService(event_repo)
    
    metrics = await analytics_service.get_analytics(
        event_name=event,
        date_from=parsed_from,
        date_to=parsed_to
    )

    # 3. Format response properties
    return AnalyticsResponse(
        totalEvents=metrics["total_events"],
        eventsPerUser=metrics["events_per_user"],
        mostActiveUsers=metrics["most_active_users"]
    )
