from pydantic import BaseModel
from datetime import datetime

class CommentModel(BaseModel):
    comment_id: str
    event_id: str
    user_id: str
    content: str
    created_at: datetime
