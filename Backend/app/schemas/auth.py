from pydantic import BaseModel, Field, field_validator
from typing import Optional

from app.schemas.validators import validate_http_url


class ProfileCompletionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=1, le=6, description="Academic year (1-6)")
    department: str = Field(..., min_length=1, max_length=100)
    profile_picture: Optional[str] = None

    @field_validator("name", "department")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("profile_picture")
    @classmethod
    def _url(cls, v: Optional[str]) -> Optional[str]:
        return validate_http_url(v)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    profile_completed: bool


class GoogleAuthInitResponse(BaseModel):
    authorization_url: str
