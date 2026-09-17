from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class EventModel(BaseModel):
    event_id: str
    title: str
    description: str
    category: str
    host_id: str
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    venue: str
    registration_url: Optional[str] = None
    poster_url: Optional[str] = None
    tags: List[str] = []
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
