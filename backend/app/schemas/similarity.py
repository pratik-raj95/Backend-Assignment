from typing import Optional
from pydantic import BaseModel, Field

class SimilarUserDetail(BaseModel):
    userId: str = Field(..., description="Unique User ID of the matched profile")
    similarity_score: float = Field(..., description="Cosine similarity score between behavior centroids [0.0 - 1.0]")
    total_events: int = Field(..., description="Total events tracked for this user")
    last_active: Optional[str] = Field(None, description="ISO timestamp of last activity recorded")
