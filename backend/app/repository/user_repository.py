import datetime
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieves a user profile by their ID.
        """
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_id: str) -> User:
        """
        Creates a new user record.
        """
        user = User(id=user_id, total_events=0)
        self.session.add(user)
        await self.session.flush()  # flush to DB within transaction
        return user

    async def upsert_user_activity(self, user_id: str, timestamp: Optional[datetime.datetime] = None) -> User:
        """
        Atomically updates user event counts and activity timestamp.
        Creates the user if they do not yet exist.
        """
        if timestamp is None:
            timestamp = datetime.datetime.now(datetime.timezone.utc)

        # PostgreSQL-specific insert upsert statement
        stmt = insert(User).values(
            id=user_id,
            total_events=1,
            last_active=timestamp
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[User.id],
            set_={
                "total_events": User.total_events + 1,
                "last_active": stmt.excluded.last_active
            }
        )
        await self.session.execute(stmt)
        await self.session.flush()

        # Return updated user
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_all_users(self) -> list[User]:
        """
        Retrieves all user records.
        """
        query = select(User)
        result = await self.session.execute(query)
        return list(result.scalars().all())
