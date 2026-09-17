import uuid
from datetime import datetime, timezone

def generate_user_id() -> str:
    return f"USR_{uuid.uuid4().hex[:8].upper()}"

def generate_event_id() -> str:
    return f"EV_{uuid.uuid4().hex[:8].upper()}"

def generate_comment_id() -> str:
    return f"CM_{uuid.uuid4().hex[:8].upper()}"

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
