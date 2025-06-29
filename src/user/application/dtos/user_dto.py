from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class UserCreateDTO(BaseModel):
    """DTO for creating a new user."""
    email: str = Field(..., description="User email address")
    name: str = Field(..., min_length=2, max_length=100, description="User full name")
    password: str = Field(..., min_length=8, description="User password")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Invalid email format')
        return v.lower().strip()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class UserUpdateDTO(BaseModel):
    """DTO for updating an existing user."""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="User full name")
    is_active: Optional[bool] = Field(None, description="User active status")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else None


class UserChangePasswordDTO(BaseModel):
    """DTO for changing user password."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class UserResponseDTO(BaseModel):
    """DTO for user response data."""
    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class UserListResponseDTO(BaseModel):
    """DTO for paginated user list response."""
    users: list[UserResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int