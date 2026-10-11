from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_active_user, get_optional_user
from app.routes.formatters import event_fields, format_event_response
from app.schemas.common import ApiResponse
from app.schemas.event import (
    EVENT_CATEGORIES,
    EventCategoriesResponse,
    EventCreateRequest,
    EventDetailResponse,
    EventResponse,
)
from app.services.event_service import EventService
from app.utils.errors import NotFoundError

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.post("", response_model=ApiResponse[EventResponse], status_code=status.HTTP_201_CREATED, summary="Submit / Host an Event")
async def create_event(
    body: EventCreateRequest,
    current_user: dict = Depends(get_current_active_user)
):
    created_event = await EventService.create_event(body.model_dump(), host_id=current_user["user_id"])
    created_event["host_name"] = current_user.get("name")
    return ApiResponse(
        message="Event submitted successfully and is pending admin approval",
        data=format_event_response(created_event)
    )


@router.get("/categories", response_model=ApiResponse[EventCategoriesResponse], summary="List Event Categories")
async def get_categories():
    return ApiResponse(message="Categories", data=EventCategoriesResponse(categories=EVENT_CATEGORIES))


@router.get("", response_model=ApiResponse[List[EventResponse]], summary="Get Approved Public Events")
async def get_events(
    category: Optional[str] = None,
    date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    search: Optional[str] = Query(None, max_length=100),
    upcoming_only: bool = False,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    viewer: Optional[dict] = Depends(get_optional_user),
):
    events = await EventService.get_approved_events(
        category=category, date=date, search=search, upcoming_only=upcoming_only,
        page=page, limit=limit, viewer_id=viewer["user_id"] if viewer else None,
    )
    return ApiResponse(message="Approved events retrieved", data=[format_event_response(e) for e in events])


@router.get("/upcoming", response_model=ApiResponse[List[EventResponse]], summary="Get Upcoming Approved Events")
async def get_upcoming_events(
    limit: int = Query(10, ge=1, le=50),
    viewer: Optional[dict] = Depends(get_optional_user),
):
    events = await EventService.get_upcoming_events(
        limit=limit, viewer_id=viewer["user_id"] if viewer else None
    )
    return ApiResponse(message="Upcoming events retrieved", data=[format_event_response(e) for e in events])


@router.get("/my-hosted", response_model=ApiResponse[List[EventResponse]], summary="Get Events Submitted by Me")
async def get_my_hosted_events(current_user: dict = Depends(get_current_active_user)):
    events = await EventService.get_hosted_by_user(current_user["user_id"])
    return ApiResponse(message="My hosted events retrieved", data=[format_event_response(e) for e in events])


@router.get("/registered", response_model=ApiResponse[List[EventResponse]], summary="Get Events I Registered For")
async def get_my_registered_events(current_user: dict = Depends(get_current_active_user)):
    events = await EventService.get_registered_by_user(current_user["user_id"])
    return ApiResponse(message="My registered events retrieved", data=[format_event_response(e) for e in events])


@router.get("/{event_id}", response_model=ApiResponse[EventDetailResponse], summary="Get Event Details (Mongo + Neo4j Interaction Stats)")
async def get_event_detail(
    event_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    try:
        event = await EventService.get_event_detail(event_id, current_user_id=current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # Unapproved events are visible only to their host or an admin. Respond 404
    # (not 403) so the existence of other people's drafts is not disclosed.
    is_owner = event["host_id"] == current_user["user_id"]
    if event["status"] != "approved" and not is_owner and current_user.get("role") != "ADMIN":
        raise NotFoundError("Event not found")

    detail = EventDetailResponse(
        **event_fields(event),
        view_count=event.get("view_count", 0),
        share_count=event.get("share_count", 0),
    )
    return ApiResponse(message="Event details retrieved", data=detail)


def _interaction_response(event_id: str, message: str, **flags) -> ApiResponse[dict]:
    return ApiResponse(message=message, data={"event_id": event_id, **flags})


@router.post("/{event_id}/like", response_model=ApiResponse[dict], summary="Like Event")
async def like_event(event_id: str, current_user: dict = Depends(get_current_active_user)):
    try:
        await EventService.like_event(current_user["user_id"], current_user.get("name", ""), event_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _interaction_response(event_id, "Event liked successfully", liked=True)


@router.delete("/{event_id}/like", response_model=ApiResponse[dict], summary="Unlike Event")
async def unlike_event(event_id: str, current_user: dict = Depends(get_current_active_user)):
    await EventService.unlike_event(current_user["user_id"], event_id)
    return _interaction_response(event_id, "Event unliked successfully", liked=False)


@router.post("/{event_id}/register", response_model=ApiResponse[dict], summary="Register for Event")
async def register_event(event_id: str, current_user: dict = Depends(get_current_active_user)):
    try:
        await EventService.register_event(current_user["user_id"], current_user.get("name", ""), event_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _interaction_response(event_id, "Registered for event successfully", registered=True)


@router.delete("/{event_id}/register", response_model=ApiResponse[dict], summary="Unregister from Event")
async def unregister_event(event_id: str, current_user: dict = Depends(get_current_active_user)):
    await EventService.unregister_event(current_user["user_id"], event_id)
    return _interaction_response(event_id, "Unregistered from event successfully", registered=False)


@router.post("/{event_id}/view", response_model=ApiResponse[dict], summary="Record Event View")
async def record_view(event_id: str, current_user: dict = Depends(get_current_active_user)):
    try:
        await EventService.record_view(current_user["user_id"], current_user.get("name", ""), event_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _interaction_response(event_id, "View recorded")


@router.post("/{event_id}/share", response_model=ApiResponse[dict], summary="Record Event Share")
async def record_share(event_id: str, current_user: dict = Depends(get_current_active_user)):
    try:
        await EventService.record_share(current_user["user_id"], current_user.get("name", ""), event_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _interaction_response(event_id, "Share recorded")
