"""Shared conversion of stored Mongo documents to API response models."""
from typing import Any, Dict

from app.schemas.event import EventResponse


def iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def event_fields(e: Dict[str, Any]) -> Dict[str, Any]:
    return dict(
        event_id=e["event_id"],
        title=e["title"],
        description=e["description"],
        category=e["category"],
        host_id=e["host_id"],
        host_name=e.get("host_name"),
        date=e["date"],
        start_time=e["start_time"],
        end_time=e["end_time"],
        venue=e["venue"],
        registration_url=e.get("registration_url"),
        poster_url=e.get("poster_url"),
        tags=e.get("tags", []),
        status=e["status"],
        rejection_reason=e.get("rejection_reason"),
        created_at=iso(e["created_at"]),
        like_count=e.get("like_count", 0),
        registration_count=e.get("registration_count", 0),
        is_liked_by_me=e.get("is_liked_by_me", False),
        is_registered_by_me=e.get("is_registered_by_me", False),
    )


def format_event_response(e: Dict[str, Any]) -> EventResponse:
    return EventResponse(**event_fields(e))
