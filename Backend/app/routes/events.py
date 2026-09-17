from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional

from app.schemas.event import EventCreateRequest, EventResponse, EventDetailResponse
from app.schemas.common import ApiResponse
from app.services.event_service import EventService
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/api/events", tags=["Events"])

def format_event_response(e: dict) -> EventResponse:
    return EventResponse(
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
        created_at=e["created_at"].isoformat() if hasattr(e["created_at"], "isoformat") else str(e["created_at"])
    )

@router.post("", response_model=ApiResponse[EventResponse], status_code=status.HTTP_201_CREATED, summary="Submit / Host an Event")
async def create_event(
    body: EventCreateRequest,
    current_user: dict = Depends(get_current_active_user)
):
    event_data = body.model_dump()
    created_event = await EventService.create_event(event_data, host_id=current_user["user_id"])
    created_event["host_name"] = current_user.get("name")
    return ApiResponse(
        message="Event submitted successfully and is pending admin approval",
        data=format_event_response(created_event)
    )

@router.get("", response_model=ApiResponse[List[EventResponse]], summary="Get Approved Public Events")
async def get_events(
    category: Optional[str] = None,
    date: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    events = await EventService.get_approved_events(
        category=category, date=date, search=search, page=page, limit=limit
    )
    data = [format_event_response(e) for e in events]
    return ApiResponse(message="Approved events retrieved", data=data)

@router.get("/upcoming", response_model=ApiResponse[List[EventResponse]], summary="Get Upcoming Approved Events")
async def get_upcoming_events(limit: int = Query(10, ge=1, le=50)):
    events = await EventService.get_upcoming_events(limit=limit)
    data = [format_event_response(e) for e in events]
    return ApiResponse(message="Upcoming events retrieved", data=data)

@router.get("/my-hosted", response_model=ApiResponse[List[EventResponse]], summary="Get Events Submitted by Me")
async def get_my_hosted_events(current_user: dict = Depends(get_current_active_user)):
    events = await EventService.get_hosted_by_user(current_user["user_id"])
    for e in events:
        e["host_name"] = current_user.get("name")
    data = [format_event_response(e) for e in events]
    return ApiResponse(message="My hosted events retrieved", data=data)

@router.get("/{event_id}", response_model=ApiResponse[EventDetailResponse], summary="Get Event Details (Mongo + Neo4j Interaction Stats)")
async def get_event_detail(
    event_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    try:
        event = await EventService.get_event_detail(event_id, current_user_id=current_user["user_id"])
        
        # Access control: Unapproved events only visible to host or admin
        if event["status"] != "approved" and event["host_id"] != current_user["user_id"] and current_user.get("role") != "ADMIN":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Event is pending approval and not publicly visible")

        detail = EventDetailResponse(
            **format_event_response(event).model_dump(),
            like_count=event.get("like_count", 0),
            registration_count=event.get("registration_count", 0),
            view_count=event.get("view_count", 0),
            share_count=event.get("share_count", 0),
            is_liked_by_me=event.get("is_liked_by_me", False),
            is_registered_by_me=event.get("is_registered_by_me", False),
            social_context=event.get("social_context")
        )
        return ApiResponse(message="Event details retrieved", data=detail)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{event_id}/like", response_model=ApiResponse[dict], summary="Like Event")
async def like_event(
    event_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    try:
        await EventService.like_event(current_user["user_id"], current_user.get("name", ""), event_id)
        return ApiResponse(message="Event liked successfully", data={"event_id": event_id, "liked": True})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{event_id}/like", response_model=ApiResponse[dict], summary="Unlike Event")
async def unlike_event(
    event_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    await EventService.unlike_event(current_user["user_id"], event_id)
    return ApiResponse(message="Event unliked successfully", data={"event_id": event_id, "liked": False})

@router.post("/{event_id}/register", response_model=ApiResponse[dict], summary="Register for Event")
async def register_event(
    event_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    try:
        await EventService.register_event(current_user["user_id"], current_user.get("name", ""), event_id)
        return ApiResponse(message="Registered for event successfully", data={"event_id": event_id, "registered": True})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{event_id}/register", response_model=ApiResponse[dict], summary="Unregister from Event")
async def unregister_event(
    event_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    await EventService.unregister_event(current_user["user_id"], event_id)
    return ApiResponse(message="Unregistered from event successfully", data={"event_id": event_id, "registered": False})

@router.post("/{event_id}/view", response_model=ApiResponse[dict], summary="Record Event View")
async def record_view(
    event_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    try:
        await EventService.record_view(current_user["user_id"], current_user.get("name", ""), event_id)
        return ApiResponse(message="View recorded", data={"event_id": event_id})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{event_id}/share", response_model=ApiResponse[dict], summary="Record Event Share")
async def record_share(
    event_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    try:
        await EventService.record_share(current_user["user_id"], current_user.get("name", ""), event_id)
        return ApiResponse(message="Share recorded", data={"event_id": event_id})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
