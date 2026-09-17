from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from typing import Optional

from app.config import get_settings
from app.schemas.auth import ProfileCompletionRequest, AuthTokenResponse, GoogleAuthInitResponse
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.get("/google/login", summary="Redirect to Google OAuth 2.0 Login")
async def google_login(state: Optional[str] = "default_state", redirect: bool = Query(True)):
    auth_url = AuthService.get_google_login_url(state=state)
    if redirect:
        return RedirectResponse(url=auth_url)
    return ApiResponse(message="OAuth authorization URL generated", data={"authorization_url": auth_url})

@router.get("/google/callback", summary="Google OAuth 2.0 Callback")
async def google_callback(code: str = Query(...), state: Optional[str] = None):
    settings = get_settings()
    try:
        user_info = await AuthService.exchange_google_code(code)
        user_doc, access_token = await AuthService.process_google_user(user_info)
        
        # Redirect to frontend depending on profile completion status
        if user_doc.get("profile_completed", False):
            redirect_target = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
        else:
            redirect_target = f"{settings.FRONTEND_URL}/complete-profile?token={access_token}"
            
        return RedirectResponse(url=redirect_target)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google authentication failed: {str(e)}"
        )

@router.post("/complete-profile", response_model=ApiResponse[AuthTokenResponse], summary="Complete Profile for First-time Google Login")
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
        return ApiResponse(
            message="Profile completed successfully",
            data=AuthTokenResponse(
                access_token=new_token,
                user_id=updated_user["user_id"],
                role=updated_user["role"],
                profile_completed=True
            )
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
