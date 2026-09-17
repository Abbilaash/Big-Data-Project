from pydantic import BaseModel, Field
from typing import Optional

class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

class CommentResponse(BaseModel):
    comment_id: str
    event_id: str
    user_id: str
    user_name: Optional[str] = None
    user_picture: Optional[str] = None
    content: str
    created_at: str
