from typing import Dict, List, Any
from pydantic import BaseModel, Field

class ActiveUserDetail(BaseModel):
    userId: str = Field(..., alias="userId")
    count: int = Field(..., description="Number of events logged by the user")

    class Config:
        populate_by_name = True

class AnalyticsResponse(BaseModel):
    totalEvents: int = Field(..., description="Sum of tracked events matching filters")
    eventsPerUser: Dict[str, int] = Field(..., description="Event count mapping per user ID")
    mostActiveUsers: List[ActiveUserDetail] = Field(..., description="Top active user statistics")
