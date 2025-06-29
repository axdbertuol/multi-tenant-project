from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class RoleCreateDTO(BaseModel):
    """DTO for creating a new role."""

    name: str = Field(..., min_length=2, max_length=50, description="Role name")
    description: str = Field(..., max_length=500, description="Role description")
    organization_id: Optional[UUID] = Field(
        None, description="Organization ID (None for global roles)"
    )
    parent_role_id: Optional[UUID] = Field(
        None, description="Parent role ID for inheritance"
    )
    permission_ids: List[UUID] = Field(
        default_factory=list, description="Initial permissions to assign"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Role name cannot be empty")
        # Convert to lowercase with underscores
        return v.strip().lower().replace(" ", "_").replace("-", "_")


class RoleUpdateDTO(BaseModel):
    """DTO for updating an existing role."""

    description: Optional[str] = Field(
        None, max_length=500, description="Role description"
    )
    permission_ids: Optional[List[UUID]] = Field(
        None, description="Permissions to assign (replaces current)"
    )


class RolePermissionAssignDTO(BaseModel):
    """DTO for assigning permissions to a role."""

    permission_ids: List[UUID] = Field(..., description="Permission IDs to assign")


class RolePermissionRemoveDTO(BaseModel):
    """DTO for removing permissions from a role."""

    permission_ids: List[UUID] = Field(..., description="Permission IDs to remove")


class RoleInheritanceDTO(BaseModel):
    """DTO for setting role inheritance."""

    parent_role_id: UUID = Field(..., description="Parent role ID")


class RoleHierarchyResponseDTO(BaseModel):
    """DTO for role hierarchy response."""

    roles: List["RoleResponseDTO"]
    hierarchy_tree: dict
    validation_errors: List[str] = Field(default_factory=list)


class RoleResponseDTO(BaseModel):
    """DTO for role response data."""

    id: UUID
    name: str
    description: str
    organization_id: Optional[UUID] = None
    parent_role_id: Optional[UUID] = None
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    is_system_role: bool
    permission_count: int
    assignment_count: int
    has_children: bool = False
    inheritance_level: int = 0

    model_config = {"from_attributes": True}


class RoleDetailResponseDTO(RoleResponseDTO):
    """DTO for detailed role response with permissions."""

    permissions: List["PermissionResponseDTO"]


class RoleListResponseDTO(BaseModel):
    """DTO for paginated role list response."""

    roles: List[RoleResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


# Forward reference import
from .permission_dto import PermissionResponseDTO

RoleDetailResponseDTO.model_rebuild()
