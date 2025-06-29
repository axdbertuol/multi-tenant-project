from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class OrganizationCreateDTO(BaseModel):
    """DTO for creating a new organization."""
    name: str = Field(..., min_length=2, max_length=100, description="Organization name")
    description: Optional[str] = Field(None, max_length=500, description="Organization description")
    max_users: int = Field(10, ge=1, le=1000, description="Maximum users allowed")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Organization name cannot be empty')
        return v.strip()


class OrganizationUpdateDTO(BaseModel):
    """DTO for updating an existing organization."""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Organization name")
    description: Optional[str] = Field(None, max_length=500, description="Organization description")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('Organization name cannot be empty')
        return v.strip() if v else None


class OrganizationSettingsUpdateDTO(BaseModel):
    """DTO for updating organization settings."""
    max_users: Optional[int] = Field(None, ge=1, le=1000, description="Maximum users allowed")
    allow_user_registration: Optional[bool] = Field(None, description="Allow user registration")
    require_email_verification: Optional[bool] = Field(None, description="Require email verification")
    session_timeout_hours: Optional[int] = Field(None, ge=1, le=720, description="Session timeout in hours")
    features_enabled: Optional[Dict[str, bool]] = Field(None, description="Enabled features")
    custom_settings: Optional[Dict[str, Any]] = Field(None, description="Custom settings")


class OrganizationResponseDTO(BaseModel):
    """DTO for organization response data."""
    id: UUID
    name: str
    description: Optional[str] = None
    owner_id: UUID
    max_users: int
    current_user_count: int
    settings: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class OrganizationListResponseDTO(BaseModel):
    """DTO for paginated organization list response."""
    organizations: list[OrganizationResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class OrganizationMemberSummaryDTO(BaseModel):
    """DTO for organization member summary."""
    user_id: UUID
    user_name: str
    user_email: str
    role: str
    joined_at: datetime
    is_active: bool


class OrganizationDetailResponseDTO(OrganizationResponseDTO):
    """DTO for detailed organization response with members."""
    members: list[OrganizationMemberSummaryDTO]
    member_count: int
    roles_distribution: Dict[str, int]