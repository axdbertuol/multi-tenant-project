from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID
from pydantic import BaseModel, Field

from ...domain.value_objects.folder_permission_level import FolderPermissionLevel


class ProfileFolderPermissionCreateDTO(BaseModel):
    """DTO for creating a new profile folder permission."""

    profile_id: UUID = Field(..., description="Profile ID")
    folder_path: str = Field(..., description="Folder path")
    permission_level: FolderPermissionLevel = Field(..., description="Permission level")
    organization_id: UUID = Field(..., description="Organization ID")
    created_by: UUID = Field(..., description="ID of user creating the permission")
    notes: Optional[str] = Field(None, description="Permission notes")
    extra_data: Optional[dict] = Field(None, description="Additional extra data")


class ProfileFolderPermissionUpdateDTO(BaseModel):
    """DTO for updating an existing profile folder permission."""

    permission_level: Optional[FolderPermissionLevel] = Field(None, description="New permission level")
    folder_path: Optional[str] = Field(None, description="New folder path")
    is_active: Optional[bool] = Field(None, description="Active status")
    notes: Optional[str] = Field(None, description="Permission notes")
    extra_data: Optional[dict] = Field(None, description="Additional extra data")


class ProfileFolderPermissionResponseDTO(BaseModel):
    """DTO for profile folder permission response data."""

    id: UUID
    profile_id: UUID
    folder_path: str
    permission_level: FolderPermissionLevel
    organization_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    notes: Optional[str] = None
    extra_data: dict = Field(default_factory=dict)
    
    # Related data
    profile_name: Optional[str] = None
    profile_description: Optional[str] = None
    created_by_name: Optional[str] = None
    organization_name: Optional[str] = None
    
    # Computed fields
    permission_level_display: Optional[str] = None
    permission_level_description: Optional[str] = None
    allowed_actions: Optional[List[str]] = None
    folder_depth: Optional[int] = None
    relative_path: Optional[str] = None
    folder_name: Optional[str] = None
    status: Optional[str] = None
    
    # Capability flags
    can_create_folders: Optional[bool] = None
    can_edit_documents: Optional[bool] = None
    can_read_documents: Optional[bool] = None
    can_use_rag: Optional[bool] = None
    can_train_rag: Optional[bool] = None

    model_config = {"from_attributes": True}


class ProfileFolderPermissionDetailResponseDTO(ProfileFolderPermissionResponseDTO):
    """DTO for detailed profile folder permission response."""

    profile: "ProfileResponseDTO"
    created_by_user: "UserInfoDTO"
    parent_folder_path: Optional[str] = None
    child_folders: List[str] = Field(default_factory=list)
    conflicting_permissions: List[UUID] = Field(default_factory=list)
    hierarchical_permissions: List["ProfileFolderPermissionResponseDTO"] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
    is_root_folder: bool
    creation_age_days: int
    last_update_age_days: Optional[int] = None
    is_recently_created: bool
    is_recently_updated: bool


class ProfileFolderPermissionListResponseDTO(BaseModel):
    """DTO for paginated profile folder permission list response."""

    permissions: List[ProfileFolderPermissionResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProfileFolderPermissionStatsDTO(BaseModel):
    """DTO for profile folder permission statistics."""

    total_permissions: int
    active_permissions: int
    inactive_permissions: int
    permissions_by_level: Dict[str, int]
    permissions_by_folder: Dict[str, int]
    permissions_by_profile: Dict[str, int]
    permissions_by_creator: Dict[str, int]
    root_folder_permissions: int
    deep_folder_permissions: int
    recent_permissions: List[ProfileFolderPermissionResponseDTO]
    most_used_folders: List[tuple[str, int]]
    permission_level_distribution: Dict[str, float]


class ProfileFolderPermissionFilterDTO(BaseModel):
    """DTO for filtering profile folder permissions."""

    profile_id: Optional[UUID] = Field(None, description="Filter by profile ID")
    folder_path: Optional[str] = Field(None, description="Filter by folder path")
    folder_path_prefix: Optional[str] = Field(None, description="Filter by folder path prefix")
    permission_level: Optional[FolderPermissionLevel] = Field(None, description="Filter by permission level")
    organization_id: Optional[UUID] = Field(None, description="Filter by organization ID")
    created_by: Optional[UUID] = Field(None, description="Filter by creator user ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_root_folder: Optional[bool] = Field(None, description="Filter root folder permissions")
    min_folder_depth: Optional[int] = Field(None, description="Filter by minimum folder depth")
    max_folder_depth: Optional[int] = Field(None, description="Filter by maximum folder depth")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date")
    updated_after: Optional[datetime] = Field(None, description="Filter by update date")
    updated_before: Optional[datetime] = Field(None, description="Filter by update date")


class ProfileFolderPermissionSearchDTO(BaseModel):
    """DTO for searching profile folder permissions."""

    query: str = Field(..., min_length=1, description="Search query")
    search_fields: List[str] = Field(
        default_factory=lambda: ["folder_path", "profile_name", "notes"],
        description="Fields to search in"
    )
    filters: Optional[ProfileFolderPermissionFilterDTO] = Field(None, description="Additional filters")


class ProfileFolderPermissionBulkActionDTO(BaseModel):
    """DTO for bulk actions on profile folder permissions."""

    permission_ids: List[UUID] = Field(..., description="Permission IDs to act on")
    action: str = Field(..., description="Action to perform: activate, deactivate, update_level, delete")
    performed_by: UUID = Field(..., description="ID of user performing the action")
    new_permission_level: Optional[FolderPermissionLevel] = Field(None, description="New permission level (for update_level action)")
    reason: Optional[str] = Field(None, description="Reason for the action")


class ProfileFolderPermissionBulkActionResponseDTO(BaseModel):
    """DTO for bulk action response."""

    success_count: int
    failure_count: int
    errors: List[str] = Field(default_factory=list)
    affected_permissions: List[UUID]
    warnings: List[str] = Field(default_factory=list)


class ProfileFolderPermissionBatchCreateDTO(BaseModel):
    """DTO for creating multiple profile folder permissions."""

    permissions: List[ProfileFolderPermissionCreateDTO]
    organization_id: UUID
    created_by: UUID
    skip_existing: bool = Field(False, description="Whether to skip existing permissions")
    skip_conflicts: bool = Field(False, description="Whether to skip conflicting permissions")


class ProfileFolderPermissionBatchCreateResponseDTO(BaseModel):
    """DTO for batch create response."""

    created_count: int
    skipped_count: int
    conflict_count: int
    error_count: int
    created_permissions: List[ProfileFolderPermissionResponseDTO] = Field(default_factory=list)
    skipped_permissions: List[str] = Field(default_factory=list)
    conflicting_permissions: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class ProfileFolderPermissionValidationDTO(BaseModel):
    """DTO for validating profile folder permissions."""

    profile_id: UUID
    folder_path: str
    permission_level: FolderPermissionLevel
    organization_id: UUID
    check_conflicts: bool = Field(True, description="Whether to check for conflicts")
    check_hierarchy: bool = Field(True, description="Whether to check folder hierarchy")


class ProfileFolderPermissionValidationResponseDTO(BaseModel):
    """DTO for validation response."""

    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    conflicts: List[UUID] = Field(default_factory=list)
    hierarchy_issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class UserFolderAccessDTO(BaseModel):
    """DTO for checking user folder access."""

    user_id: UUID
    folder_path: str
    organization_id: UUID
    requested_action: Optional[str] = Field(None, description="Specific action to check")


class UserFolderAccessResponseDTO(BaseModel):
    """DTO for user folder access response."""

    user_id: UUID
    folder_path: str
    can_access: bool
    permission_level: Optional[FolderPermissionLevel] = None
    allowed_actions: List[str] = Field(default_factory=list)
    access_reason: Optional[str] = None
    applicable_profiles: List[str] = Field(default_factory=list)
    applicable_permissions: List[UUID] = Field(default_factory=list)


class FolderPermissionMatrixDTO(BaseModel):
    """DTO for folder permission matrix."""

    organization_id: UUID
    folder_paths: Optional[List[str]] = Field(None, description="Specific folder paths")
    profile_ids: Optional[List[UUID]] = Field(None, description="Specific profile IDs")
    include_inactive: bool = Field(False, description="Whether to include inactive permissions")


class FolderPermissionMatrixResponseDTO(BaseModel):
    """DTO for folder permission matrix response."""

    organization_id: UUID
    matrix: Dict[str, Dict[str, str]] = Field(default_factory=dict)  # folder_path -> profile_name -> permission_level
    folder_paths: List[str] = Field(default_factory=list)
    profile_names: List[str] = Field(default_factory=list)
    permission_summary: Dict[str, int] = Field(default_factory=dict)
    generated_at: datetime


class ProfileFolderPermissionImportDTO(BaseModel):
    """DTO for importing profile folder permissions."""

    permissions: List[ProfileFolderPermissionCreateDTO]
    organization_id: UUID
    imported_by: UUID
    overwrite_existing: bool = Field(False, description="Whether to overwrite existing permissions")
    resolve_conflicts: bool = Field(False, description="Whether to resolve conflicts automatically")
    validation_mode: str = Field("strict", description="Validation mode (strict, lenient, skip)")


class ProfileFolderPermissionImportResponseDTO(BaseModel):
    """DTO for import response."""

    imported_count: int
    skipped_count: int
    conflict_count: int
    error_count: int
    imported_permissions: List[ProfileFolderPermissionResponseDTO] = Field(default_factory=list)
    skipped_permissions: List[str] = Field(default_factory=list)
    conflicting_permissions: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ProfileFolderPermissionCleanupDTO(BaseModel):
    """DTO for cleaning up profile folder permissions."""

    organization_id: UUID
    cleanup_type: str = Field("orphaned", description="Type of cleanup (orphaned, conflicts, duplicates)")
    profile_ids: Optional[List[UUID]] = Field(None, description="Specific profile IDs to clean")
    dry_run: bool = Field(True, description="Whether to only simulate the cleanup")
    performed_by: UUID = Field(..., description="ID of user performing the cleanup")


class ProfileFolderPermissionCleanupResponseDTO(BaseModel):
    """DTO for cleanup response."""

    cleanup_type: str
    affected_count: int
    cleaned_permissions: List[UUID] = Field(default_factory=list)
    dry_run: bool
    summary: Dict[str, int] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


# Forward reference imports
from .profile_dto import ProfileResponseDTO
from .user_profile_dto import UserInfoDTO

ProfileFolderPermissionDetailResponseDTO.model_rebuild()