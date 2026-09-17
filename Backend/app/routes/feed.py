from fastapi import APIRouter, Depends, Query
from typing import List

from app.schemas.social import FeedItemResponse, SocialContext, FeedUserAction
from app.schemas.common import ApiResponse
from app.services.feed_service import FeedService
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/api/feed", tags=["Feed"])

@router.get("", response_model=ApiResponse[List[FeedItemResponse]], summary="Get Personalized Hybrid Social Feed")
async def get_social_feed(
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_active_user)
):
    feed_events = await FeedService.get_personalized_feed(
        user_id=current_user["user_id"],
        limit=limit
    )

    feed_items = []
    for e in feed_events:
        sc_data = e.get("social_context")
        social_context = None
        if sc_data:
            social_context = SocialContext(
                reason=sc_data["reason"],
                users=[
                    FeedUserAction(
                        user_id=u["user_id"],
                        name=u["name"],
                        action=u["action"]
                    )
                    for u in sc_data["users"]
                ]
            )

        feed_items.append(
            FeedItemResponse(
                event_id=e["event_id"],
                title=e["title"],
                description=e["description"],
                category=e["category"],
                host_id=e["host_id"],
                date=e["date"],
                start_time=e["start_time"],
                end_time=e["end_time"],
                venue=e["venue"],
                registration_url=e.get("registration_url"),
                poster_url=e.get("poster_url"),
                tags=e.get("tags", []),
                status=e["status"],
                created_at=e["created_at"].isoformat() if hasattr(e["created_at"], "isoformat") else str(e["created_at"]),
                social_context=social_context
            )
        )

    return ApiResponse(message="Personalized feed generated", data=feed_items)
