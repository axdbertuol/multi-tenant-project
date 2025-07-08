from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ManagementFunctionCreateDTO(BaseModel):
    """DTO for creating a new management function."""

    name: str = Field(..., min_length=2, max_length=50, description="Function name")
    description: str = Field(..., max_length=500, description="Function description")
    organization_id: UUID = Field(..., description="Organization ID")
    permissions: List[str] = Field(
        default_factory=list, description="Initial permissions to assign"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Function name cannot be empty")
        # Convert to lowercase with underscores
        return v.strip().lower().replace(" ", "_").replace("-", "_")

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: List[str]) -> List[str]:
        if not v:
            return []
        # Validate permission format (should be management permissions)
        for perm in v:
            if not perm.startswith("management."):
                raise ValueError(f"Invalid permission format: {perm}. Must start with 'management.'")
        return v


class ManagementFunctionUpdateDTO(BaseModel):
    """DTO for updating an existing management function."""

    description: Optional[str] = Field(
        None, max_length=500, description="Function description"
    )
    permissions: Optional[List[str]] = Field(
        None, description="Permissions to assign (replaces current)"
    )

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        # Validate permission format (should be management permissions)
        for perm in v:
            if not perm.startswith("management."):
                raise ValueError(f"Invalid permission format: {perm}. Must start with 'management.'")
        return v


class ManagementFunctionPermissionAssignDTO(BaseModel):
    """DTO for assigning permissions to a management function."""

    permissions: List[str] = Field(..., description="Permissions to assign")

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: List[str]) -> List[str]:
        for perm in v:
            if not perm.startswith("management."):
                raise ValueError(f"Invalid permission format: {perm}. Must start with 'management.'")
        return v


class ManagementFunctionPermissionRemoveDTO(BaseModel):
    """DTO for removing permissions from a management function."""

    permissions: List[str] = Field(..., description="Permissions to remove")


class ManagementFunctionAssignmentDTO(BaseModel):
    """DTO for assigning a management function to a user."""

    user_id: UUID = Field(..., description="User ID")
    area_id: UUID = Field(..., description="Document area ID")
    assigned_by: UUID = Field(..., description="ID of user making the assignment")


class ManagementFunctionResponseDTO(BaseModel):
    """DTO for management function response data."""

    id: UUID
    name: str
    description: str
    organization_id: UUID
    permissions: List[str]
    created_at: datetime
    is_active: bool
    is_system_function: bool
    assignment_count: int = 0

    model_config = {"from_attributes": True}


class ManagementFunctionDetailResponseDTO(ManagementFunctionResponseDTO):
    """DTO for detailed management function response with assignments."""

    assignments: List["UserFunctionAreaResponseDTO"]


class ManagementFunctionListResponseDTO(BaseModel):
    """DTO for paginated management function list response."""

    functions: List[ManagementFunctionResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class ManagementFunctionStatsDTO(BaseModel):
    """DTO for management function statistics."""

    total_functions: int
    active_functions: int
    system_functions: int
    custom_functions: int
    total_assignments: int
    functions_by_permission: dict[str, int]


# Forward reference import
from .user_function_area_dto import UserFunctionAreaResponseDTO

ManagementFunctionDetailResponseDTO.model_rebuild()