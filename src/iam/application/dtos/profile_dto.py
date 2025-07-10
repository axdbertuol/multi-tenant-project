from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class ProfileCreateDTO(BaseModel):
    """DTO for creating a new profile."""

    name: str = Field(..., min_length=1, max_length=100, description="Profile name")
    description: str = Field(..., max_length=500, description="Profile description")
    organization_id: UUID = Field(..., description="Organization ID")
    created_by: UUID = Field(..., description="ID of user creating the profile")
    is_system_profile: bool = Field(
        False, description="Whether this is a system profile"
    )
    profile_metadata: Optional[dict] = Field(
        None, description="Additional profile_metadata"
    )


class ProfileUpdateDTO(BaseModel):
    """DTO for updating an existing profile."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="New profile name"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="New profile description"
    )
    is_active: Optional[bool] = Field(None, description="Active status")
    profile_metadata: Optional[dict] = Field(
        None, description="Additional profile_metadata"
    )


class ProfileResponseDTO(BaseModel):
    """DTO for profile response data."""

    id: UUID
    name: str
    description: str
    organization_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    is_system_profile: bool
    profile_metadata: dict = Field(default_factory=dict)

    # Related data
    created_by_name: Optional[str] = None
    organization_name: Optional[str] = None
    user_count: Optional[int] = None
    permission_count: Optional[int] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}


class ProfileDetailResponseDTO(ProfileResponseDTO):
    """DTO for detailed profile response."""

    permissions: List["ProfileFolderPermissionResponseDTO"] = Field(
        default_factory=list
    )
    users: List["UserProfileResponseDTO"] = Field(default_factory=list)
    creation_age_days: int
    last_update_age_days: Optional[int] = None
    is_recently_created: bool
    is_recently_updated: bool
    can_be_deleted: bool
    can_be_modified: bool
    validation_errors: List[str] = Field(default_factory=list)


class ProfileListResponseDTO(BaseModel):
    """DTO for paginated profile list response."""

    profiles: List[ProfileResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProfileStatsDTO(BaseModel):
    """DTO for profile statistics."""

    total_profiles: int
    active_profiles: int
    inactive_profiles: int
    system_profiles: int
    user_profiles: int
    profiles_with_users: int
    profiles_with_permissions: int
    profiles_by_creator: dict[str, int]
    recent_profiles: List[ProfileResponseDTO]
    most_used_profiles: List[tuple[ProfileResponseDTO, int]]


class ProfileFilterDTO(BaseModel):
    """DTO for filtering profiles."""

    name: Optional[str] = Field(None, description="Filter by profile name")
    organization_id: Optional[UUID] = Field(
        None, description="Filter by organization ID"
    )
    created_by: Optional[UUID] = Field(None, description="Filter by creator user ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_system_profile: Optional[bool] = Field(
        None, description="Filter by system profile status"
    )
    created_after: Optional[datetime] = Field(
        None, description="Filter by creation date"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter by creation date"
    )
    updated_after: Optional[datetime] = Field(None, description="Filter by update date")
    updated_before: Optional[datetime] = Field(
        None, description="Filter by update date"
    )
    has_users: Optional[bool] = Field(
        None, description="Filter profiles with/without users"
    )
    has_permissions: Optional[bool] = Field(
        None, description="Filter profiles with/without permissions"
    )
    profile_metadata_key: Optional[str] = Field(None, description="Filter by profile metadata key")
    profile_metadata_value: Optional[str] = Field(None, description="Filter by profile metadata value")


class ProfileSearchDTO(BaseModel):
    """DTO for searching profiles."""

    query: str = Field(..., min_length=1, description="Search query")
    search_fields: List[str] = Field(
        default_factory=lambda: ["name", "description"],
        description="Fields to search in",
    )
    filters: Optional[ProfileFilterDTO] = Field(None, description="Additional filters")


class ProfileBulkActionDTO(BaseModel):
    """DTO for bulk actions on profiles."""

    profile_ids: List[UUID] = Field(..., description="Profile IDs to act on")
    action: str = Field(
        ..., description="Action to perform: activate, deactivate, delete"
    )
    performed_by: UUID = Field(..., description="ID of user performing the action")
    reason: Optional[str] = Field(None, description="Reason for the action")


class ProfileBulkActionResponseDTO(BaseModel):
    """DTO for bulk action response."""

    success_count: int
    failure_count: int
    errors: List[str] = Field(default_factory=list)
    affected_profiles: List[UUID]
    warnings: List[str] = Field(default_factory=list)


class ProfileImportDTO(BaseModel):
    """DTO for importing profiles."""

    profiles: List[ProfileCreateDTO]
    organization_id: UUID
    imported_by: UUID
    overwrite_existing: bool = Field(
        False, description="Whether to overwrite existing profiles"
    )
    validate_only: bool = Field(
        False, description="Whether to only validate without importing"
    )


class ProfileImportResponseDTO(BaseModel):
    """DTO for profile import response."""

    imported_count: int
    skipped_count: int
    error_count: int
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    imported_profiles: List[ProfileResponseDTO] = Field(default_factory=list)
    skipped_profiles: List[str] = Field(default_factory=list)


class ProfileExportDTO(BaseModel):
    """DTO for exporting profiles."""

    organization_id: UUID
    profile_ids: Optional[List[UUID]] = Field(
        None, description="Specific profile IDs to export"
    )
    include_permissions: bool = Field(
        True, description="Whether to include permissions"
    )
    include_users: bool = Field(True, description="Whether to include user assignments")
    include_profile_metadata: bool = Field(True, description="Whether to include profile metadata")
    format: str = Field("json", description="Export format (json, csv, xlsx)")


class ProfileExportResponseDTO(BaseModel):
    """DTO for profile export response."""

    exported_count: int
    export_format: str
    file_name: str
    file_size: int
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class ProfileValidationDTO(BaseModel):
    """DTO for profile validation."""

    profile_id: UUID
    validation_type: str = Field(
        "full", description="Validation type (full, basic, permissions)"
    )
    fix_issues: bool = Field(False, description="Whether to auto-fix fixable issues")


class ProfileValidationResponseDTO(BaseModel):
    """DTO for profile validation response."""

    is_valid: bool
    validation_type: str
    issues: List[dict] = Field(default_factory=list)
    fixed_issues: List[dict] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class ProfileCloneDTO(BaseModel):
    """DTO for cloning a profile."""

    source_profile_id: UUID
    new_name: str = Field(..., min_length=1, max_length=100)
    new_description: Optional[str] = Field(None, max_length=500)
    target_organization_id: Optional[UUID] = Field(
        None, description="Target organization (if different)"
    )
    clone_permissions: bool = Field(True, description="Whether to clone permissions")
    clone_users: bool = Field(False, description="Whether to clone user assignments")
    clone_profile_metadata: bool = Field(True, description="Whether to clone profile metadata")
    cloned_by: UUID = Field(..., description="ID of user performing the clone")


class ProfileCloneResponseDTO(BaseModel):
    """DTO for profile clone response."""

    original_profile: ProfileResponseDTO
    cloned_profile: ProfileResponseDTO
    cloned_permissions_count: int
    cloned_users_count: int
    warnings: List[str] = Field(default_factory=list)


class ProfileUsageStatsDTO(BaseModel):
    """DTO for profile usage statistics."""

    profile_id: UUID
    profile_name: str
    active_users: int
    inactive_users: int
    total_users: int
    permissions_count: int
    folders_accessible: int
    last_assignment_date: Optional[datetime] = None
    most_recent_user: Optional[str] = None
    usage_score: float = Field(description="Usage score (0-100)")
    recommendations: List[str] = Field(default_factory=list)


class ProfileComparisonDTO(BaseModel):
    """DTO for comparing profiles."""

    profile1_id: UUID
    profile2_id: UUID
    comparison_type: str = Field("permissions", description="Type of comparison")


class ProfileComparisonResponseDTO(BaseModel):
    """DTO for profile comparison response."""

    profile1: ProfileResponseDTO
    profile2: ProfileResponseDTO
    comparison_type: str
    similarities: List[dict] = Field(default_factory=list)
    differences: List[dict] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


# Forward reference imports
from .user_profile_dto import UserProfileResponseDTO
from .profile_folder_permission_dto import ProfileFolderPermissionResponseDTO

ProfileDetailResponseDTO.model_rebuild()
