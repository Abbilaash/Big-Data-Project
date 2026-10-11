import logging
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.schemas.auth import ProfileCompletionRequest, AuthTokenResponse
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService
from app.dependencies import get_current_user
from app.utils.security import create_oauth_state, verify_oauth_state

logger = logging.getLogger("campusconnect.routes.auth")

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _frontend_redirect(path: str, **fragment: str) -> RedirectResponse:
    """Redirect to the SPA, carrying values in the URL fragment.

    Fragments are never sent to servers or included in Referer headers, unlike
    query strings, so the token does not leak into logs.
    """
    base = get_settings().primary_frontend_url
    target = f"{base}{path}"
    if fragment:
        target += "#" + urlencode(fragment)
    return RedirectResponse(url=target, status_code=status.HTTP_302_FOUND)


@router.get("/config", summary="Public auth configuration for the login screen")
async def auth_config():
    return ApiResponse(
        message="Auth configuration",
        data={"dev_login_enabled": get_settings().dev_login_enabled},
    )


@router.get("/google/login", summary="Redirect to Google OAuth 2.0 Login")
async def google_login(redirect: bool = Query(True)):
    auth_url = AuthService.get_google_login_url(state=create_oauth_state())
    if redirect:
        return RedirectResponse(url=auth_url)
    return ApiResponse(message="OAuth authorization URL generated", data={"authorization_url": auth_url})


@router.get("/google/callback", summary="Google OAuth 2.0 Callback")
async def google_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    if error:
        return _frontend_redirect("/login", error="Google sign-in was cancelled or denied.")
    if not code or not verify_oauth_state(state):
        return _frontend_redirect("/login", error="Sign-in session expired or invalid. Please try again.")
    try:
        user_info = await AuthService.exchange_google_code(code)
        user_doc, access_token = await AuthService.process_google_user(user_info)
    except ValueError as e:
        logger.warning(f"Google sign-in rejected: {e}")
        return _frontend_redirect("/login", error="Google sign-in could not be completed.")
    except Exception:
        logger.exception("Unexpected failure during Google callback")
        return _frontend_redirect("/login", error="Sign-in is temporarily unavailable. Please try again.")

    return _frontend_redirect(
        "/auth/callback",
        token=access_token,
        profile_completed="true" if user_doc.get("profile_completed") else "false",
    )


class DevLoginRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+$", max_length=254)
    name: str = Field(..., min_length=1, max_length=100)


@router.post("/dev-login", response_model=ApiResponse[AuthTokenResponse], summary="Development-only login (disabled by default)")
async def dev_login(body: DevLoginRequest):
    if not get_settings().dev_login_enabled:
        # Indistinguishable from a missing route so it is not advertised.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    email = body.email.lower()
    user_doc, token = await AuthService.process_google_user(
        {"id": f"dev:{email}", "email": email, "name": body.name, "picture": ""}
    )
    return ApiResponse(
        message="Development login successful",
        data=AuthTokenResponse(
            access_token=token,
            user_id=user_doc["user_id"],
            role=user_doc["role"],
            profile_completed=bool(user_doc.get("profile_completed")),
        ),
    )


@router.get("/session", summary="Basic identity for the signed-in user, even before the profile is complete")
async def session_info(current_user: dict = Depends(get_current_user)):
    return ApiResponse(
        message="Session",
        data={
            "user_id": current_user["user_id"],
            "email": current_user["email"],
            "name": current_user.get("name", ""),
            "profile_picture": current_user.get("profile_picture"),
            "role": current_user["role"],
            "profile_completed": bool(current_user.get("profile_completed")),
        },
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
