from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_active_user
from app.routes.formatters import iso
from app.schemas.common import ApiResponse
from app.schemas.social import SocialUserResponse
from app.schemas.user import PublicUserResponse, UserProfileResponse, UserProfileUpdateRequest
from app.services.social_service import SocialService
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])


def _profile_response(u: dict) -> UserProfileResponse:
    return UserProfileResponse(
        user_id=u["user_id"],
        email=u["email"],
        name=u["name"],
        year=u.get("year"),
        department=u.get("department"),
        profile_picture=u.get("profile_picture"),
        role=u["role"],
        profile_completed=u.get("profile_completed", True),
        created_at=iso(u["created_at"]),
    )


@router.get("/me", response_model=ApiResponse[UserProfileResponse], summary="Get Current User Profile")
async def get_my_profile(current_user: dict = Depends(get_current_active_user)):
    return ApiResponse(message="Profile retrieved", data=_profile_response(current_user))


@router.patch("/me", response_model=ApiResponse[UserProfileResponse], summary="Update Current User Profile")
async def update_my_profile(
    body: UserProfileUpdateRequest,
    current_user: dict = Depends(get_current_active_user)
):
    updates = body.model_dump(exclude_unset=True)
    updates = {k: v for k, v in updates.items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update")

    updated_user = await UserService.update_profile(current_user["user_id"], updates)
    return ApiResponse(message="Profile updated successfully", data=_profile_response(updated_user))


@router.get("", response_model=ApiResponse[List[SocialUserResponse]], summary="People Directory")
async def list_people(
    q: Optional[str] = Query(None, max_length=100),
    department: Optional[str] = Query(None, max_length=100),
    year: Optional[int] = Query(None, ge=1, le=6),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=50),
    current_user: dict = Depends(get_current_active_user),
):
    people = await SocialService.list_people(
        current_user["user_id"], q=q, department=department, year=year, page=page, limit=limit
    )
    return ApiResponse(message="People retrieved", data=people)


@router.get("/departments", response_model=ApiResponse[List[str]], summary="Departments in Use")
async def list_departments(current_user: dict = Depends(get_current_active_user)):
    return ApiResponse(message="Departments", data=await SocialService.list_departments())


@router.get("/suggestions", response_model=ApiResponse[List[SocialUserResponse]], summary="People You May Know")
async def get_suggestions(
    limit: int = Query(12, ge=1, le=30),
    current_user: dict = Depends(get_current_active_user),
):
    return ApiResponse(
        message="Suggestions",
        data=await SocialService.get_suggestions(current_user["user_id"], limit=limit),
    )


@router.get("/search", response_model=ApiResponse[List[SocialUserResponse]], summary="Search Users")
async def search_users(
    q: str = Query(..., min_length=1, max_length=100),
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
    followers = await SocialService.get_followers(user_id, viewer_id=current_user["user_id"])
    return ApiResponse(message="Followers list retrieved", data=followers)


@router.get("/{user_id}/following", response_model=ApiResponse[List[SocialUserResponse]], summary="Get User Following List")
async def get_user_following(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    following = await SocialService.get_following(user_id, viewer_id=current_user["user_id"])
    return ApiResponse(message="Following list retrieved", data=following)
