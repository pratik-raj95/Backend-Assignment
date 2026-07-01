import uuid
import datetime
from typing import Dict, Any
from sqlalchemy import String, ForeignKey, Boolean, Index, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    total_events: Mapped[int] = mapped_column(Integer, default=0)
    last_active: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_name: Mapped[str] = mapped_column(String, nullable=False)
    metadata_: Mapped[Dict[str, Any]] = mapped_column(JSONB, name="metadata", default=dict)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    embedding_status: Mapped[bool] = mapped_column(Boolean, default=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    user = relationship("User", back_populates="events")
    vector_mapping = relationship("VectorMapping", back_populates="event", cascade="all, delete-orphan", uselist=False)

    __table_args__ = (
        Index("idx_events_user_id", "user_id"),
        Index("idx_events_timestamp", "timestamp"),
        Index("idx_events_event_name", "event_name"),
    )

class VectorMapping(Base):
    __tablename__ = "vector_mapping"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), unique=True, nullable=False)
    vector_index: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    event = relationship("Event", back_populates="vector_mapping")
