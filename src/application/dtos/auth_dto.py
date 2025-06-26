from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class SignupDto(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)


class LoginDto(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class AuthResponseDto(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserInfoDto"


class UserInfoDto(BaseModel):
    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class TokenPayloadDto(BaseModel):
    user_id: UUID
    email: str
    session_id: Optional[UUID] = None
    exp: datetime
    iat: datetime