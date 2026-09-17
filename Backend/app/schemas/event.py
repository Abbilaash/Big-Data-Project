from pydantic import BaseModel, Field
from typing import Optional, List, Any

class EventCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    category: str = Field(..., min_length=2, max_length=50)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD format")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    venue: str = Field(..., min_length=2, max_length=150)
    registration_url: Optional[str] = None
    poster_url: Optional[str] = None
    tags: List[str] = []

class EventResponse(BaseModel):
    event_id: str
    title: str
    description: str
    category: str
    host_id: str
    host_name: Optional[str] = None
    date: str
    start_time: str
    end_time: str
    venue: str
    registration_url: Optional[str] = None
    poster_url: Optional[str] = None
    tags: List[str] = []
    status: str
    created_at: str

class EventDetailResponse(EventResponse):
    like_count: int = 0
    registration_count: int = 0
    view_count: int = 0
    share_count: int = 0
    is_liked_by_me: bool = False
    is_registered_by_me: bool = False
    social_context: Optional[Any] = None
