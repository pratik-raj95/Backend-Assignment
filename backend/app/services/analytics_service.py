import datetime
from typing import Optional, Dict, Any
from app.repository.event_repository import EventRepository
from app.core.logger import logger

class AnalyticsService:
    """
    Coordinates metrics aggregations.
    """
    def __init__(self, event_repository: EventRepository):
        self.event_repo = event_repository

    async def get_analytics(
        self,
        event_name: Optional[str] = None,
        date_from: Optional[datetime.datetime] = None,
        date_to: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        """
        Retrieves user behavior statistics by running aggregate queries in DB.
        """
        logger.info("Running aggregate analytics query in DB.")
        metrics = await self.event_repo.get_analytics_metrics(
            event_name=event_name,
            date_from=date_from,
            date_to=date_to
        )
        return metrics
