from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.schemas.event import EventResponse
from app.schemas.admin import EventRejectionRequest, EventAnalyticsResponse, NetworkAnalyticsResponse
from app.schemas.common import ApiResponse
from app.services.admin_service import AdminService
from app.services.event_service import EventService
from app.dependencies import get_current_admin
from app.routes.events import format_event_response

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/events/pending", response_model=ApiResponse[List[EventResponse]], summary="Get Pending Events for Moderation")
async def get_pending_events(current_admin: dict = Depends(get_current_admin)):
    events = await AdminService.get_pending_events()
    data = [format_event_response(e) for e in events]
    return ApiResponse(message="Pending events retrieved", data=data)

@router.get("/events/{event_id}", response_model=ApiResponse[EventResponse], summary="Inspect Event for Moderation")
async def inspect_event(
    event_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    event = await EventService.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return ApiResponse(message="Event details for admin", data=format_event_response(event))

@router.post("/events/{event_id}/approve", response_model=ApiResponse[EventResponse], summary="Approve Pending Event")
async def approve_event(
    event_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    try:
        approved_event = await AdminService.approve_event(event_id, admin_id=current_admin["user_id"])
        return ApiResponse(message="Event approved and added to graph", data=format_event_response(approved_event))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/events/{event_id}/reject", response_model=ApiResponse[EventResponse], summary="Reject Pending Event")
async def reject_event(
    event_id: str,
    body: Optional[EventRejectionRequest] = None,
    current_admin: dict = Depends(get_current_admin)
):
    try:
        reason = body.rejection_reason if body else None
        rejected_event = await AdminService.reject_event(event_id, admin_id=current_admin["user_id"], reason=reason)
        return ApiResponse(message="Event rejected", data=format_event_response(rejected_event))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/analytics/events", response_model=ApiResponse[EventAnalyticsResponse], summary="Get MongoDB Event Aggregation Analytics")
async def get_event_analytics(current_admin: dict = Depends(get_current_admin)):
    analytics = await AdminService.get_event_analytics()
    return ApiResponse(message="Event aggregation analytics generated", data=EventAnalyticsResponse(**analytics))

@router.get("/analytics/network", response_model=ApiResponse[NetworkAnalyticsResponse], summary="Get Neo4j Graph Network Analytics")
async def get_network_analytics(current_admin: dict = Depends(get_current_admin)):
    analytics = await AdminService.get_network_analytics()
    return ApiResponse(message="Network graph analytics generated", data=NetworkAnalyticsResponse(**analytics))
