from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class UserProfileCreateDTO(BaseModel):
    """DTO for creating a new user profile assignment."""

    user_id: UUID = Field(..., description="User ID")
    profile_id: UUID = Field(..., description="Profile ID")
    organization_id: UUID = Field(..., description="Organization ID")
    assigned_by: UUID = Field(..., description="ID of user making the assignment")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    notes: Optional[str] = Field(None, description="Assignment notes")
    extra_data: Optional[dict] = Field(None, description="Additional extra data")


class UserProfileUpdateDTO(BaseModel):
    """DTO for updating an existing user profile assignment."""

    profile_id: Optional[UUID] = Field(None, description="New profile ID")
    expires_at: Optional[datetime] = Field(None, description="New expiration date")
    is_active: Optional[bool] = Field(None, description="Active status")
    notes: Optional[str] = Field(None, description="Assignment notes")
    extra_data: Optional[dict] = Field(None, description="Additional extra data")


class UserProfileExtendDTO(BaseModel):
    """DTO for extending user profile assignment."""

    new_expires_at: Optional[datetime] = Field(None, description="New expiration date (None for permanent)")
    extended_by: UUID = Field(..., description="ID of user extending the assignment")
    reason: Optional[str] = Field(None, description="Reason for extension")


class UserProfileRevokeDTO(BaseModel):
    """DTO for revoking user profile assignment."""

    revoked_by: UUID = Field(..., description="ID of user revoking the assignment")
    reason: Optional[str] = Field(None, description="Reason for revocation")


class UserProfileResponseDTO(BaseModel):
    """DTO for user profile assignment response data."""

    id: UUID
    user_id: UUID
    profile_id: UUID
    organization_id: UUID
    assigned_by: UUID
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None
    notes: Optional[str] = None
    extra_data: dict = Field(default_factory=dict)
    
    # Related data
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    profile_name: Optional[str] = None
    profile_description: Optional[str] = None
    assigned_by_name: Optional[str] = None
    organization_name: Optional[str] = None
    
    # Computed fields
    status: Optional[str] = None
    assignment_type: Optional[str] = None
    days_until_expiry: Optional[int] = None
    is_expired: Optional[bool] = None
    is_expiring_soon: Optional[bool] = None
    assignment_duration_days: Optional[int] = None

    model_config = {"from_attributes": True}


class UserProfileDetailResponseDTO(UserProfileResponseDTO):
    """DTO for detailed user profile assignment response."""

    profile: "ProfileResponseDTO"
    user: "UserInfoDTO"
    assigned_by_user: "UserInfoDTO"
    revoked_by_user: Optional["UserInfoDTO"] = None
    effective_permissions: List[str] = Field(default_factory=list)
    accessible_folders: List[str] = Field(default_factory=list)
    folder_permissions: List["ProfileFolderPermissionResponseDTO"] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
    can_be_modified: bool
    can_be_deleted: bool
    modification_reason: Optional[str] = None
    deletion_reason: Optional[str] = None


class UserProfileListResponseDTO(BaseModel):
    """DTO for paginated user profile assignment list response."""

    assignments: List[UserProfileResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserProfileStatsDTO(BaseModel):
    """DTO for user profile assignment statistics."""

    total_assignments: int
    active_assignments: int
    inactive_assignments: int
    expired_assignments: int
    expiring_soon_assignments: int
    revoked_assignments: int
    temporary_assignments: int
    permanent_assignments: int
    assignments_by_profile: dict[str, int]
    assignments_by_user: dict[str, int]
    assignments_by_assigner: dict[str, int]
    recent_assignments: List[UserProfileResponseDTO]
    expiring_assignments: List[UserProfileResponseDTO]


class UserProfileFilterDTO(BaseModel):
    """DTO for filtering user profile assignments."""

    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    profile_id: Optional[UUID] = Field(None, description="Filter by profile ID")
    organization_id: Optional[UUID] = Field(None, description="Filter by organization ID")
    assigned_by: Optional[UUID] = Field(None, description="Filter by assigned by user")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_expired: Optional[bool] = Field(None, description="Filter by expiration status")
    is_revoked: Optional[bool] = Field(None, description="Filter by revocation status")
    assignment_type: Optional[str] = Field(None, description="Filter by assignment type (temporary/permanent)")
    status: Optional[str] = Field(None, description="Filter by status")
    assigned_after: Optional[datetime] = Field(None, description="Filter by assignment date")
    assigned_before: Optional[datetime] = Field(None, description="Filter by assignment date")
    expires_after: Optional[datetime] = Field(None, description="Filter by expiration date")
    expires_before: Optional[datetime] = Field(None, description="Filter by expiration date")
    expiring_within_days: Optional[int] = Field(None, description="Filter assignments expiring within N days")


class UserProfileSearchDTO(BaseModel):
    """DTO for searching user profile assignments."""

    query: str = Field(..., min_length=1, description="Search query")
    search_fields: List[str] = Field(
        default_factory=lambda: ["user_name", "user_email", "profile_name", "notes"],
        description="Fields to search in"
    )
    filters: Optional[UserProfileFilterDTO] = Field(None, description="Additional filters")


class UserProfileBulkActionDTO(BaseModel):
    """DTO for bulk actions on user profile assignments."""

    assignment_ids: List[UUID] = Field(..., description="Assignment IDs to act on")
    action: str = Field(..., description="Action to perform: activate, deactivate, extend, revoke, delete")
    performed_by: UUID = Field(..., description="ID of user performing the action")
    new_expires_at: Optional[datetime] = Field(None, description="New expiration date (for extend action)")
    reason: Optional[str] = Field(None, description="Reason for the action")


class UserProfileBulkActionResponseDTO(BaseModel):
    """DTO for bulk action response."""

    success_count: int
    failure_count: int
    errors: List[str] = Field(default_factory=list)
    affected_assignments: List[UUID]
    warnings: List[str] = Field(default_factory=list)


class UserProfileBatchCreateDTO(BaseModel):
    """DTO for creating multiple user profile assignments."""

    assignments: List[UserProfileCreateDTO]
    organization_id: UUID
    assigned_by: UUID
    default_expires_at: Optional[datetime] = Field(None, description="Default expiration for all assignments")
    skip_existing: bool = Field(False, description="Whether to skip existing assignments")


class UserProfileBatchCreateResponseDTO(BaseModel):
    """DTO for batch create response."""

    created_count: int
    skipped_count: int
    error_count: int
    created_assignments: List[UserProfileResponseDTO] = Field(default_factory=list)
    skipped_assignments: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class UserProfileTransferDTO(BaseModel):
    """DTO for transferring user assignments between profiles."""

    user_ids: List[UUID] = Field(..., description="User IDs to transfer")
    source_profile_id: UUID = Field(..., description="Source profile ID")
    target_profile_id: UUID = Field(..., description="Target profile ID")
    organization_id: UUID = Field(..., description="Organization ID")
    transferred_by: UUID = Field(..., description="ID of user making the transfer")
    preserve_expiration: bool = Field(True, description="Whether to preserve expiration dates")
    transfer_reason: Optional[str] = Field(None, description="Reason for transfer")


class UserProfileTransferResponseDTO(BaseModel):
    """DTO for transfer response."""

    transferred_count: int
    skipped_count: int
    error_count: int
    transferred_assignments: List[UserProfileResponseDTO] = Field(default_factory=list)
    skipped_users: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class UserProfileHistoryDTO(BaseModel):
    """DTO for user profile assignment history."""

    user_id: UUID
    profile_id: UUID
    organization_id: UUID
    include_revoked: bool = Field(True, description="Whether to include revoked assignments")
    include_expired: bool = Field(True, description="Whether to include expired assignments")
    date_from: Optional[datetime] = Field(None, description="Start date for history")
    date_to: Optional[datetime] = Field(None, description="End date for history")


class UserProfileHistoryResponseDTO(BaseModel):
    """DTO for assignment history response."""

    user_id: UUID
    profile_id: UUID
    history: List[UserProfileResponseDTO]
    total_assignments: int
    current_assignment: Optional[UserProfileResponseDTO] = None
    last_active_assignment: Optional[UserProfileResponseDTO] = None
    assignment_timeline: List[dict] = Field(default_factory=list)


class UserProfileAuditDTO(BaseModel):
    """DTO for user profile assignment audit."""

    assignment_id: UUID
    action: str  # "created", "updated", "revoked", "extended", "deleted"
    performed_by: UUID
    timestamp: datetime
    old_values: Optional[dict] = Field(None, description="Previous values")
    new_values: Optional[dict] = Field(None, description="New values")
    reason: Optional[str] = Field(None, description="Reason for the action")
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent")


class UserProfileCleanupDTO(BaseModel):
    """DTO for cleaning up user profile assignments."""

    organization_id: UUID
    cleanup_type: str = Field("expired", description="Type of cleanup (expired, revoked, old)")
    days_threshold: int = Field(30, description="Days threshold for cleanup")
    dry_run: bool = Field(True, description="Whether to only simulate the cleanup")
    performed_by: UUID = Field(..., description="ID of user performing the cleanup")


class UserProfileCleanupResponseDTO(BaseModel):
    """DTO for cleanup response."""

    cleanup_type: str
    affected_count: int
    cleaned_assignments: List[UUID] = Field(default_factory=list)
    dry_run: bool
    summary: dict = Field(default_factory=dict)


class UserContextDTO(BaseModel):
    """DTO for user context with profile information."""

    user_id: UUID
    organization_id: UUID
    active_profiles: List[UserProfileResponseDTO] = Field(default_factory=list)
    effective_permissions: List[str] = Field(default_factory=list)
    accessible_folders: List[str] = Field(default_factory=list)
    folder_permissions: dict[str, str] = Field(default_factory=dict)  # folder_path -> permission_level
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    last_updated: datetime


class UserInfoDTO(BaseModel):
    """DTO for user information in profile context."""

    id: UUID
    name: str
    email: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Forward reference imports
from .profile_dto import ProfileResponseDTO
from .profile_folder_permission_dto import ProfileFolderPermissionResponseDTO

UserProfileDetailResponseDTO.model_rebuild()