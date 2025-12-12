from pydantic import BaseModel
from typing import Optional

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    station_id: Optional[int] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True
