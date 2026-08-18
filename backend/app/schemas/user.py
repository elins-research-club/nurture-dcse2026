from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
