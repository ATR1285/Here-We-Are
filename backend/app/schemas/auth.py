from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role_name: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role_id: str
    is_active: bool
    
    class Config:
        from_attributes = True

class SessionInfo(BaseModel):
    id: str
    expires_at: datetime
    is_revoked: bool
