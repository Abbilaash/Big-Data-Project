from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class EventRejectionRequest(BaseModel):
    rejection_reason: Optional[str] = None

class EventAnalyticsResponse(BaseModel):
    total_events: int
    approved_events: int
    pending_events: int
    rejected_events: int
    by_category: Dict[str, int]
    events_by_host: List[Dict[str, Any]]

class NetworkAnalyticsResponse(BaseModel):
    total_users: int
    total_follows: int
    most_followed_users: List[Dict[str, Any]]
    most_interacted_events: List[Dict[str, Any]]
