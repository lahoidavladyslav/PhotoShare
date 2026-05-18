from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.db.models import Role


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=255)

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: str | None = None  
    role: Role
    confirmed: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"