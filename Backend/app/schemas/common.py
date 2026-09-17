from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: Optional[T] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: Optional[Any] = None
