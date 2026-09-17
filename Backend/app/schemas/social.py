from pydantic import BaseModel
from typing import List, Optional
from app.schemas.event import EventResponse

class FollowStatusResponse(BaseModel):
    target_user_id: str
    is_following: bool

class SocialUserResponse(BaseModel):
    user_id: str
    name: str
    department: Optional[str] = None
    profile_picture: Optional[str] = None

class FeedUserAction(BaseModel):
    user_id: str
    name: str
    action: str

class SocialContext(BaseModel):
    reason: str
    users: List[FeedUserAction]

class FeedItemResponse(BaseModel):
    event_id: str
    title: str
    description: str
    category: str
    host_id: str
    date: str
    start_time: str
    end_time: str
    venue: str
    registration_url: Optional[str] = None
    poster_url: Optional[str] = None
    tags: List[str] = []
    status: str
    created_at: str
    social_context: Optional[SocialContext] = None

class CommonInterestResponse(BaseModel):
    event_id: str
    title: str
    category: str
    interaction_type: str
