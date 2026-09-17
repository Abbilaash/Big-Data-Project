from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.schemas.comment import CommentCreateRequest, CommentResponse
from app.schemas.common import ApiResponse
from app.services.comment_service import CommentService
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/api/events", tags=["Comments"])

def format_comment_response(c: dict) -> CommentResponse:
    return CommentResponse(
        comment_id=c["comment_id"],
        event_id=c["event_id"],
        user_id=c["user_id"],
        user_name=c.get("user_name"),
        user_picture=c.get("user_picture"),
        content=c["content"],
        created_at=c["created_at"].isoformat() if hasattr(c["created_at"], "isoformat") else str(c["created_at"])
    )

@router.post("/{event_id}/comments", response_model=ApiResponse[CommentResponse], status_code=status.HTTP_201_CREATED, summary="Add Comment to Event")
async def add_comment(
    event_id: str,
    body: CommentCreateRequest,
    current_user: dict = Depends(get_current_active_user)
):
    try:
        comment = await CommentService.add_comment(
            event_id=event_id,
            user_id=current_user["user_id"],
            content=body.content
        )
        return ApiResponse(message="Comment added successfully", data=format_comment_response(comment))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{event_id}/comments", response_model=ApiResponse[List[CommentResponse]], summary="Get Comments for Event")
async def get_comments(
    event_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    comments = await CommentService.get_event_comments(event_id)
    data = [format_comment_response(c) for c in comments]
    return ApiResponse(message="Event comments retrieved", data=data)
