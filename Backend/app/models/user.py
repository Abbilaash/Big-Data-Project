from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserModel(BaseModel):
    user_id: str
    google_id: Optional[str] = None
    email: EmailStr
    name: str
    year: Optional[int] = None
    department: Optional[str] = None
    profile_picture: Optional[str] = None
    role: str = "USER"  # USER or ADMIN
    profile_completed: bool = False
    created_at: datetime
    updated_at: datetime
