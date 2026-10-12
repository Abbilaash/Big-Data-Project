import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.schemas.auth import LoginRequest, RegisterRequest, ProfileCompletionRequest, AuthTokenResponse
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService
from app.dependencies import get_current_user

logger = logging.getLogger("campusconnect.routes.auth")

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=ApiResponse[AuthTokenResponse], summary="Register a new student account")
async def register(body: RegisterRequest):
    try:
        user_doc, token = await AuthService.register_user(
            name=body.name,
            email=body.email,
            password=body.password,
            year=body.year,
            department=body.department,
            profile_picture=body.profile_picture,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during registration")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed.")

    return ApiResponse(
        message="Account created successfully",
        data=AuthTokenResponse(
            access_token=token,
            user_id=user_doc["user_id"],
            role=user_doc["role"],
            profile_completed=True,
        ),
    )


@router.post("/login", response_model=ApiResponse[AuthTokenResponse], summary="Sign in with email and password")
async def login(body: LoginRequest):
    try:
        user_doc, token = await AuthService.login_user(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception:
        logger.exception("Unexpected error during login")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Sign in failed.")

    return ApiResponse(
        message="Signed in successfully",
        data=AuthTokenResponse(
            access_token=token,
            user_id=user_doc["user_id"],
            role=user_doc["role"],
            profile_completed=bool(user_doc.get("profile_completed", True)),
        ),
    )


@router.get("/session", summary="Basic identity for the signed-in user")
async def session_info(current_user: dict = Depends(get_current_user)):
    return ApiResponse(
        message="Session",
        data={
            "user_id": current_user["user_id"],
            "email": current_user["email"],
            "name": current_user.get("name", ""),
            "profile_picture": current_user.get("profile_picture"),
            "role": current_user["role"],
            "profile_completed": bool(current_user.get("profile_completed", True)),
        },
    )


@router.post("/complete-profile", response_model=ApiResponse[AuthTokenResponse], summary="Complete or update user profile")
async def complete_profile(
    body: ProfileCompletionRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        updated_user, new_token = await AuthService.complete_profile(
            user_id=current_user["user_id"],
            name=body.name,
            year=body.year,
            department=body.department,
            profile_picture=body.profile_picture
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ApiResponse(
        message="Profile completed successfully",
        data=AuthTokenResponse(
            access_token=new_token,
            user_id=updated_user["user_id"],
            role=updated_user["role"],
            profile_completed=True
        )
    )

