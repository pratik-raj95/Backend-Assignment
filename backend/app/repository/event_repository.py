import datetime
import uuid
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import Event, VectorMapping, User

class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(
        self,
        user_id: str,
        event_name: str,
        metadata: Dict[str, Any],
        timestamp: Optional[datetime.datetime] = None
    ) -> Event:
        """
        Creates a new event record with pending embedding status.
        """
        if timestamp is None:
            timestamp = datetime.datetime.now(datetime.timezone.utc)

        event = Event(
            id=uuid.uuid4(),
            user_id=user_id,
            event_name=event_name,
            metadata_=metadata,
            timestamp=timestamp,
            embedding_status=False,
            retry_count=0
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_by_id(self, event_id: uuid.UUID) -> Optional[Event]:
        """
        Gets an event by ID.
        """
        query = select(Event).where(Event.id == event_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_events(self, limit: int = 50) -> List[Event]:
        """
        Retrieves pending events that have not been embedded and haven't exceeded retry limits.
        Used by reconciliation tasks.
        """
        query = (
            select(Event)
            .where(and_(Event.embedding_status == False, Event.retry_count < 3))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_status(self, event_id: uuid.UUID, embedding_status: bool) -> None:
        """
        Updates the embedding completion status of an event.
        """
        event = await self.get_by_id(event_id)
        if event:
            event.embedding_status = embedding_status
            await self.session.flush()

    async def increment_retry(self, event_id: uuid.UUID) -> int:
        """
        Increments the retry count for embedding generation.
        """
        event = await self.get_by_id(event_id)
        if event:
            event.retry_count += 1
            await self.session.flush()
            return event.retry_count
        return 0

    async def create_vector_mapping(self, event_id: uuid.UUID, vector_index: int) -> VectorMapping:
        """
        Saves the FAISS index row offset mapping for an event.
        """
        mapping = VectorMapping(
            id=uuid.uuid4(),
            event_id=event_id,
            vector_index=vector_index
        )
        self.session.add(mapping)
        await self.session.flush()
        return mapping

    async def get_vector_mappings_for_user(self, user_id: str) -> List[VectorMapping]:
        """
        Retrieves vector indices for all active events associated with a user.
        """
        query = (
            select(VectorMapping)
            .join(Event)
            .where(and_(Event.user_id == user_id, Event.embedding_status == True))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_events_by_vector_indices(self, vector_indices: List[int]) -> List[Tuple[Event, int]]:
        """
        Retrieves events matching specific FAISS vector index offsets.
        Returns tuples of (Event, vector_index) to preserve similarity indexing details.
        """
        if not vector_indices:
            return []
            
        query = (
            select(Event, VectorMapping.vector_index)
            .join(VectorMapping, Event.id == VectorMapping.event_id)
            .where(VectorMapping.vector_index.in_(vector_indices))
        )
        result = await self.session.execute(query)
        return list(result.all())

    async def get_analytics_metrics(
        self,
        event_name: Optional[str] = None,
        date_from: Optional[datetime.datetime] = None,
        date_to: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        """
        Queries database metrics: total events, events grouped by user, and top active users.
        """
        filters = []
        if event_name:
            filters.append(Event.event_name == event_name)
        if date_from:
            filters.append(Event.timestamp >= date_from)
        if date_to:
            filters.append(Event.timestamp <= date_to)

        # 1. Total event count
        total_stmt = select(func.count(Event.id)).where(and_(*filters))
        total_res = await self.session.execute(total_stmt)
        total_events = total_res.scalar() or 0

        # 2. Events per user
        per_user_stmt = (
            select(Event.user_id, func.count(Event.id).label("count"))
            .where(and_(*filters))
            .group_by(Event.user_id)
        )
        per_user_res = await self.session.execute(per_user_stmt)
        events_per_user = {row[0]: row[1] for row in per_user_res.all()}

        # 3. Most active users (Top 10)
        most_active_stmt = (
            select(Event.user_id, func.count(Event.id).label("count"))
            .where(and_(*filters))
            .group_by(Event.user_id)
            .order_by(func.count(Event.id).desc())
            .limit(10)
        )
        most_active_res = await self.session.execute(most_active_stmt)
        most_active_users = [{"userId": row[0], "count": row[1]} for row in most_active_res.all()]

        return {
            "total_events": total_events,
            "events_per_user": events_per_user,
            "most_active_users": most_active_users
        }

