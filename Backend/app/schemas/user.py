from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserProfileResponse(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    year: Optional[int] = None
    department: Optional[str] = None
    profile_picture: Optional[str] = None
    role: str
    profile_completed: bool
    created_at: str

class UserProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    year: Optional[int] = Field(None, ge=1, le=6)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    profile_picture: Optional[str] = None

class PublicUserResponse(BaseModel):
    user_id: str
    name: str
    year: Optional[int] = None
    department: Optional[str] = None
    profile_picture: Optional[str] = None
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
