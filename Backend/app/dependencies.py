from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any

from app.utils.security import decode_access_token
from app.database.mongodb import get_database

security_scheme = HTTPBearer(auto_error=False)

async def get_current_user_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

async def get_current_user(
    payload: Dict[str, Any] = Depends(get_current_user_token_payload)
) -> Dict[str, Any]:
    db = get_database()
    user_id = payload["user_id"]
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

async def get_current_active_user(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    if not user.get("profile_completed", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profile registration incomplete. Please complete your profile first."
        )
    return user

async def get_current_admin(
    user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    if user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user
