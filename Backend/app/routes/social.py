from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.schemas.social import FollowStatusResponse, SocialUserResponse, CommonInterestResponse
from app.schemas.common import ApiResponse
from app.services.social_service import SocialService
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/api/social", tags=["Social"])

@router.post("/follow/{user_id}", response_model=ApiResponse[FollowStatusResponse], summary="Follow a User")
async def follow_user(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    try:
        await SocialService.follow_user(follower_id=current_user["user_id"], target_id=user_id)
        return ApiResponse(
            message="User followed successfully",
            data=FollowStatusResponse(target_user_id=user_id, is_following=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/follow/{user_id}", response_model=ApiResponse[FollowStatusResponse], summary="Unfollow a User")
async def unfollow_user(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    await SocialService.unfollow_user(follower_id=current_user["user_id"], target_id=user_id)
    return ApiResponse(
        message="User unfollowed successfully",
        data=FollowStatusResponse(target_user_id=user_id, is_following=False)
    )

@router.get("/status/{user_id}", response_model=ApiResponse[FollowStatusResponse], summary="Get Follow Status")
async def get_follow_status(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    is_following = await SocialService.get_follow_status(follower_id=current_user["user_id"], target_id=user_id)
    return ApiResponse(
        message="Follow status retrieved",
        data=FollowStatusResponse(target_user_id=user_id, is_following=is_following)
    )

@router.get("/followers", response_model=ApiResponse[List[SocialUserResponse]], summary="Get My Followers")
async def get_my_followers(current_user: dict = Depends(get_current_active_user)):
    followers = await SocialService.get_followers(current_user["user_id"])
    return ApiResponse(message="My followers retrieved", data=followers)

@router.get("/following", response_model=ApiResponse[List[SocialUserResponse]], summary="Get My Following List")
async def get_my_following(current_user: dict = Depends(get_current_active_user)):
    following = await SocialService.get_following(current_user["user_id"])
    return ApiResponse(message="My following list retrieved", data=following)

@router.get("/mutuals/{user_id}", response_model=ApiResponse[List[SocialUserResponse]], summary="Get Mutual Connections")
async def get_mutual_connections(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    mutuals = await SocialService.get_mutuals(current_user["user_id"], target_id=user_id)
    return ApiResponse(message="Mutual connections retrieved", data=mutuals)

@router.get("/common-interests/{user_id}", response_model=ApiResponse[List[CommonInterestResponse]], summary="Get Common Event Interests")
async def get_common_interests(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    interests = await SocialService.get_common_interests(current_user["user_id"], target_id=user_id)
    return ApiResponse(message="Common interests retrieved", data=interests)
