import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

class EventTrackRequest(BaseModel):
    userId: str = Field(..., min_length=1, description="Unique identifier for the user", examples=["user_123"])
    event: str = Field(..., min_length=1, description="Description of the action tracked", examples=["user viewed pricing page"])
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary event metadata context")
    timestamp: Optional[datetime.datetime] = Field(None, description="Event occurrence time")

    @field_validator("timestamp", mode="before")
    @classmethod
    def set_timestamp_default(cls, v):
        if v is None:
            return datetime.datetime.now(datetime.timezone.utc)
        if isinstance(v, str):
            try:
                # Attempt to parse ISO strings, make it timezone-aware
                dt = datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                return dt
            except ValueError:
                raise ValueError("Timestamp must be a valid ISO 8601 string.")
        return v

class EventTrackResponse(BaseModel):
    success: bool
    eventId: str
    message: str
