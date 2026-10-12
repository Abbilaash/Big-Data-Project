from typing import List

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_active_user
from app.routes.formatters import event_fields
from app.schemas.common import ApiResponse
from app.schemas.social import FeedItemResponse, FeedUserAction, SocialContext
from app.services.feed_service import FeedService

router = APIRouter(prefix="/api/feed", tags=["Feed"])


@router.get("", response_model=ApiResponse[List[FeedItemResponse]], summary="Get Personalized Hybrid Social Feed")
async def get_social_feed(
    limit: int = Query(20, ge=1, le=50),
    fallback: bool = Query(True, description="Whether to include general fallback events"),
    current_user: dict = Depends(get_current_active_user)
):
    feed_events = await FeedService.get_personalized_feed(
        user_id=current_user["user_id"],
        limit=limit,
        include_fallback=fallback
    )

    items = []
    for e in feed_events:
        sc = e.get("social_context")
        social_context = (
            SocialContext(
                reason=sc["reason"],
                users=[FeedUserAction(user_id=u["user_id"], name=u["name"], action=u["action"]) for u in sc["users"]],
            )
            if sc else None
        )
        items.append(FeedItemResponse(**event_fields(e), social_context=social_context))

    return ApiResponse(message="Personalized feed generated", data=items)
