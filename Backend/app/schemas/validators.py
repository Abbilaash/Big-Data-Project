"""Reusable validation helpers shared by request schemas."""
from typing import Optional
from urllib.parse import urlparse


def validate_http_url(value: Optional[str]) -> Optional[str]:
    """Allow only absolute http(s) URLs (blocks javascript:, data:, etc.)."""
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    if len(value) > 2048:
        raise ValueError("URL is too long")
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Must be a valid http(s) URL")
    return value
