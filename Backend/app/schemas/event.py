from datetime import date as date_type, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.validators import validate_http_url

# Canonical categories. Requests are matched case-insensitively and stored in
# this canonical spelling so filters and analytics group consistently.
EVENT_CATEGORIES = [
    "Hackathon", "Workshop", "Bootcamp", "Seminar", "Contest",
    "Meetup", "Cultural", "Sports", "Other",
]


class EventCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    category: str = Field(..., min_length=2, max_length=50)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD format")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    venue: str = Field(..., min_length=2, max_length=150)
    registration_url: Optional[str] = None
    poster_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list, max_length=10)

    @field_validator("title", "description", "venue")
    @classmethod
    def _strip_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("category")
    @classmethod
    def _canonical_category(cls, v: str) -> str:
        lookup = {c.lower(): c for c in EVENT_CATEGORIES}
        canonical = lookup.get(v.strip().lower())
        if canonical is None:
            raise ValueError(f"category must be one of: {', '.join(EVENT_CATEGORIES)}")
        return canonical

    @field_validator("date")
    @classmethod
    def _real_date(cls, v: str) -> str:
        try:
            date_type.fromisoformat(v)
        except ValueError:
            raise ValueError("date is not a valid calendar date")
        return v

    @field_validator("start_time", "end_time")
    @classmethod
    def _real_time(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("time must be a valid 24-hour HH:MM value")
        return v

    @field_validator("registration_url", "poster_url")
    @classmethod
    def _url(cls, v: Optional[str]) -> Optional[str]:
        return validate_http_url(v)

    @field_validator("tags")
    @classmethod
    def _clean_tags(cls, v: List[str]) -> List[str]:
        cleaned: List[str] = []
        for tag in v:
            tag = tag.strip()
            if not tag:
                continue
            if len(tag) > 30:
                raise ValueError("each tag must be at most 30 characters")
            if tag.lower() not in {t.lower() for t in cleaned}:
                cleaned.append(tag)
        return cleaned

    @model_validator(mode="after")
    def _end_after_start(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


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
    rejection_reason: Optional[str] = None
    created_at: str
    like_count: int = 0
    registration_count: int = 0
    is_liked_by_me: bool = False
    is_registered_by_me: bool = False


class EventDetailResponse(EventResponse):
    view_count: int = 0
    share_count: int = 0
    social_context: Optional[Any] = None


class EventCategoriesResponse(BaseModel):
    categories: List[str]
