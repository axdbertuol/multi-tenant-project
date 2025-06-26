from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class CreateUserDto(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class UpdateUserDto(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class UserResponseDto(BaseModel):
    id: UUID
    email: str
    name: str
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    model_config = {"from_attributes": True}