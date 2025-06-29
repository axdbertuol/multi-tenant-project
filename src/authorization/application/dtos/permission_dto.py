from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PermissionTypeEnum(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"


class PermissionCreateDTO(BaseModel):
    """DTO for creating a new permission."""

    name: str = Field(..., min_length=3, max_length=100, description="Permission name")
    description: str = Field(..., max_length=500, description="Permission description")
    permission_type: PermissionTypeEnum = Field(..., description="Permission type")
    resource_type: str = Field(
        ..., min_length=2, max_length=50, description="Resource type"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Permission name cannot be empty")
        # Convert to lowercase with underscores/colons
        return v.strip().lower().replace(" ", "_").replace("-", "_")

    @field_validator("resource_type")
    @classmethod
    def validate_resource_type(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Resource type cannot be empty")
        return v.strip().lower().replace(" ", "_").replace("-", "_")


class PermissionResponseDTO(BaseModel):
    """DTO for permission response data."""

    id: UUID
    name: str
    description: str
    permission_type: str
    resource_type: str
    full_name: str  # resource_type:permission_type
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    is_system_permission: bool
    role_count: int  # Number of roles that have this permission

    model_config = {"from_attributes": True}


class PermissionListResponseDTO(BaseModel):
    """DTO for paginated permission list response."""

    permissions: List[PermissionResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class PermissionSearchDTO(BaseModel):
    """DTO for permission search criteria."""

    query: Optional[str] = Field(None, description="Search query")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    permission_type: Optional[PermissionTypeEnum] = Field(
        None, description="Filter by permission type"
    )
    is_active: Optional[bool] = Field(None, description="Filter by active status")
