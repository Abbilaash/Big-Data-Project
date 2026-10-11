from pydantic import BaseModel
from typing import List, Optional
from app.schemas.event import EventResponse


class FollowStatusResponse(BaseModel):
    target_user_id: str
    is_following: bool


class SocialUserResponse(BaseModel):
    user_id: str
    name: str
    year: Optional[int] = None
    department: Optional[str] = None
    profile_picture: Optional[str] = None
    is_following: Optional[bool] = None
    mutual_count: Optional[int] = None


class FeedUserAction(BaseModel):
    user_id: str
    name: str
    action: str


class SocialContext(BaseModel):
    reason: str
    users: List[FeedUserAction]


class FeedItemResponse(EventResponse):
    social_context: Optional[SocialContext] = None


class CommonInterestResponse(BaseModel):
    event_id: str
    title: str
    category: str
    interaction_type: str
