import uuid
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from app.config import get_settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        
    to_encode.update({
        "exp": expire,
        "iat": now
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return None


OAUTH_STATE_PURPOSE = "oauth_state"
OAUTH_STATE_TTL_SECONDS = 600


def create_oauth_state() -> str:
    """Short-lived signed value binding the callback to a login we started."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "purpose": OAUTH_STATE_PURPOSE,
            "nonce": uuid.uuid4().hex,
            "iat": now,
            "exp": now + timedelta(seconds=OAUTH_STATE_TTL_SECONDS),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_oauth_state(state: Optional[str]) -> bool:
    if not state:
        return False
    payload = decode_access_token(state)
    return bool(payload) and payload.get("purpose") == OAUTH_STATE_PURPOSE
