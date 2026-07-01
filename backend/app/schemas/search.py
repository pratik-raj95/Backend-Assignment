from typing import List, Dict, Any
from pydantic import BaseModel, Field

class SearchResultItem(BaseModel):
    id: str = Field(..., description="Unique event UUID")
    userId: str = Field(..., description="User ID associated with the matched event")
    event: str = Field(..., description="Event name/description content")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata attached to the event")
    timestamp: str = Field(..., description="ISO timestamp of when the event occurred")
    similarity_score: float = Field(..., description="Calculated cosine similarity value [0.0 - 1.0]")

class SearchResponse(BaseModel):
    results: List[SearchResultItem] = Field(..., description="Ranked matches sorted by similarity score")
