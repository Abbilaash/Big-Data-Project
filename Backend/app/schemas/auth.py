from pydantic import BaseModel, Field
from typing import Optional

class ProfileCompletionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=1, le=6, description="Academic year (1-6)")
    department: str = Field(..., min_length=1, max_length=100)
    profile_picture: Optional[str] = None

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    profile_completed: bool

class GoogleAuthInitResponse(BaseModel):
    authorization_url: str
