from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List

from app.schemas.user import UserProfileResponse, UserProfileUpdateRequest, PublicUserResponse
from app.schemas.social import SocialUserResponse
from app.schemas.common import ApiResponse
from app.services.user_service import UserService
from app.services.social_service import SocialService
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=ApiResponse[UserProfileResponse], summary="Get Current User Profile")
async def get_my_profile(current_user: dict = Depends(get_current_active_user)):
    return ApiResponse(
        message="Profile retrieved",
        data=UserProfileResponse(
            user_id=current_user["user_id"],
            email=current_user["email"],
            name=current_user["name"],
            year=current_user.get("year"),
            department=current_user.get("department"),
            profile_picture=current_user.get("profile_picture"),
            role=current_user["role"],
            profile_completed=current_user.get("profile_completed", True),
            created_at=current_user["created_at"].isoformat() if hasattr(current_user["created_at"], "isoformat") else str(current_user["created_at"])
        )
    )

@router.patch("/me", response_model=ApiResponse[UserProfileResponse], summary="Update Current User Profile")
async def update_my_profile(
    body: UserProfileUpdateRequest,
    current_user: dict = Depends(get_current_active_user)
):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update")

    updated_user = await UserService.update_profile(current_user["user_id"], updates)
    return ApiResponse(
        message="Profile updated successfully",
        data=UserProfileResponse(
            user_id=updated_user["user_id"],
            email=updated_user["email"],
            name=updated_user["name"],
            year=updated_user.get("year"),
            department=updated_user.get("department"),
            profile_picture=updated_user.get("profile_picture"),
            role=updated_user["role"],
            profile_completed=updated_user.get("profile_completed", True),
            created_at=updated_user["created_at"].isoformat() if hasattr(updated_user["created_at"], "isoformat") else str(updated_user["created_at"])
        )
    )

@router.get("/search", response_model=ApiResponse[List[SocialUserResponse]], summary="Search Users")
async def search_users(
    q: str = Query(..., min_length=1),
    current_user: dict = Depends(get_current_active_user)
):
    users = await UserService.search_users(q)
    return ApiResponse(message="Search results", data=users)

@router.get("/{user_id}", response_model=ApiResponse[PublicUserResponse], summary="Get Public User Profile")
async def get_user_profile(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    profile = await UserService.get_public_profile(user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return ApiResponse(message="Public profile retrieved", data=PublicUserResponse(**profile))

@router.get("/{user_id}/followers", response_model=ApiResponse[List[SocialUserResponse]], summary="Get User Followers")
async def get_user_followers(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    followers = await SocialService.get_followers(user_id)
    return ApiResponse(message="Followers list retrieved", data=followers)

@router.get("/{user_id}/following", response_model=ApiResponse[List[SocialUserResponse]], summary="Get User Following List")
async def get_user_following(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    following = await SocialService.get_following(user_id)
    return ApiResponse(message="Following list retrieved", data=following)
