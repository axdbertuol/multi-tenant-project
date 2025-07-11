from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class OrganizationRoleEnum(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class MembershipCreateDTO(BaseModel):
    """DTO for adding a user to an organization."""

    user_id: UUID = Field(..., description="User ID to add")
    role: str = Field(
        "member", description="Role to assign"
    )


class MembershipUpdateDTO(BaseModel):
    """DTO for updating a user's role in an organization."""

    role: str = Field(..., description="New role to assign")


class MembershipResponseDTO(BaseModel):
    """DTO for membership response data."""

    id: UUID
    user_id: UUID
    organization_id: UUID
    role: str
    assigned_at: datetime
    is_active: bool
    user_name: str
    user_email: str
    organization_name: str

    model_config = {"from_attributes": True}


class MembershipListResponseDTO(BaseModel):
    """DTO for paginated membership list response."""

    memberships: list[MembershipResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class OwnershipTransferDTO(BaseModel):
    """DTO for transferring organization ownership."""

    new_owner_id: UUID = Field(..., description="User ID of the new owner")

    @field_validator("new_owner_id")
    @classmethod
    def validate_new_owner_id(cls, v: UUID) -> UUID:
        if not v:
            raise ValueError("New owner ID is required")
        return v


class MembershipInviteDTO(BaseModel):
    """DTO for inviting a user to an organization."""

    email: str = Field(..., description="Email of user to invite")
    role: str = Field(
        "member", description="Role to assign"
    )
    message: Optional[str] = Field(
        None, max_length=500, description="Invitation message"
    )


class UserOrganizationSummaryDTO(BaseModel):
    """DTO for user's organization summary (simplified for 1:N relationship)."""

    organization_id: UUID
    organization_name: str
    role: str
    is_owner: bool
    joined_at: datetime
    member_count: int
    is_active: bool


class UserOrganizationsResponseDTO(BaseModel):
    """DTO for user's organization (single organization for 1:N relationship)."""

    organization: Optional[UserOrganizationSummaryDTO] = None
    has_organization: bool = False
