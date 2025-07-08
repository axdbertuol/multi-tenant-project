from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class UserDocumentAccessCreateDTO(BaseModel):
    """DTO for creating a new user document access."""

    user_id: UUID = Field(..., description="User ID")
    organization_id: UUID = Field(..., description="Organization ID")
    area_id: UUID = Field(..., description="Document area ID")
    assigned_by: UUID = Field(..., description="ID of user making the assignment")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class UserDocumentAccessUpdateDTO(BaseModel):
    """DTO for updating an existing user document access."""

    area_id: Optional[UUID] = Field(None, description="New document area ID")
    expires_at: Optional[datetime] = Field(None, description="New expiration date")
    is_active: Optional[bool] = Field(None, description="Active status")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class UserDocumentAccessBatchCreateDTO(BaseModel):
    """DTO for creating multiple user document accesses."""

    accesses: List[UserDocumentAccessCreateDTO] = Field(
        ..., description="List of accesses to create"
    )


class UserDocumentAccessBatchUpdateDTO(BaseModel):
    """DTO for batch updating user document accesses."""

    access_ids: List[UUID] = Field(..., description="Access IDs to update")
    area_id: Optional[UUID] = Field(None, description="New document area ID")
    expires_at: Optional[datetime] = Field(None, description="New expiration date")
    is_active: Optional[bool] = Field(None, description="Active status")


class UserDocumentAccessTransferDTO(BaseModel):
    """DTO for transferring user accesses between areas."""

    source_area_id: UUID = Field(..., description="Source area ID")
    target_area_id: UUID = Field(..., description="Target area ID")
    user_ids: List[UUID] = Field(..., description="User IDs to transfer")
    transferred_by: UUID = Field(..., description="ID of user making the transfer")


class UserDocumentAccessResponseDTO(BaseModel):
    """DTO for user document access response data."""

    id: UUID
    user_id: UUID
    organization_id: UUID
    area_id: UUID
    assigned_by: UUID
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    metadata: dict = Field(default_factory=dict)
    
    # Related data
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    area_name: Optional[str] = None
    area_folder_path: Optional[str] = None
    assigned_by_name: Optional[str] = None

    model_config = {"from_attributes": True}


class UserDocumentAccessDetailResponseDTO(UserDocumentAccessResponseDTO):
    """DTO for detailed user document access response."""

    area: "DocumentAreaResponseDTO"
    user: "UserInfoDTO"
    assigned_by_user: "UserInfoDTO"
    accessible_folders: List[str]
    is_expired: bool
    days_until_expiration: Optional[int] = None


class UserDocumentAccessListResponseDTO(BaseModel):
    """DTO for paginated user document access list response."""

    accesses: List[UserDocumentAccessResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserDocumentAccessStatsDTO(BaseModel):
    """DTO for user document access statistics."""

    total_accesses: int
    active_accesses: int
    expired_accesses: int
    expiring_soon_accesses: int
    accesses_by_area: dict[str, int]
    accesses_by_user: dict[str, int]
    recent_accesses: List[UserDocumentAccessResponseDTO]


class UserDocumentAccessFilterDTO(BaseModel):
    """DTO for filtering user document accesses."""

    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    organization_id: Optional[UUID] = Field(None, description="Filter by organization ID")
    area_id: Optional[UUID] = Field(None, description="Filter by area ID")
    assigned_by: Optional[UUID] = Field(None, description="Filter by assigned by user")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_expired: Optional[bool] = Field(None, description="Filter by expiration status")
    expires_after: Optional[datetime] = Field(None, description="Filter by expiration date")
    expires_before: Optional[datetime] = Field(None, description="Filter by expiration date")
    assigned_after: Optional[datetime] = Field(None, description="Filter by assignment date")
    assigned_before: Optional[datetime] = Field(None, description="Filter by assignment date")


class UserDocumentAccessSearchDTO(BaseModel):
    """DTO for searching user document accesses."""

    query: str = Field(..., min_length=1, description="Search query")
    search_fields: List[str] = Field(
        default_factory=lambda: ["user_email", "user_name", "area_name"],
        description="Fields to search in"
    )
    filters: Optional[UserDocumentAccessFilterDTO] = Field(
        None, description="Additional filters"
    )


class UserDocumentAccessBulkActionDTO(BaseModel):
    """DTO for bulk actions on user document accesses."""

    access_ids: List[UUID] = Field(..., description="Access IDs to act on")
    action: str = Field(..., description="Action to perform: activate, deactivate, delete, extend")
    new_expires_at: Optional[datetime] = Field(None, description="New expiration date for extend action")
    performed_by: UUID = Field(..., description="ID of user performing the action")


class UserDocumentAccessBulkActionResponseDTO(BaseModel):
    """DTO for bulk action response."""

    success_count: int
    failure_count: int
    errors: List[str] = Field(default_factory=list)
    affected_accesses: List[UUID]


class UserDocumentAccessRevokeDTO(BaseModel):
    """DTO for revoking user document access."""

    user_id: UUID = Field(..., description="User ID")
    organization_id: UUID = Field(..., description="Organization ID")
    revoked_by: UUID = Field(..., description="ID of user performing the revocation")
    reason: Optional[str] = Field(None, description="Reason for revocation")


class UserDocumentAccessExtendDTO(BaseModel):
    """DTO for extending user document access."""

    new_expires_at: Optional[datetime] = Field(None, description="New expiration date (None for permanent)")
    extended_by: UUID = Field(..., description="ID of user extending the access")
    reason: Optional[str] = Field(None, description="Reason for extension")


class UserDocumentAccessAuditDTO(BaseModel):
    """DTO for document access audit information."""

    user_id: UUID
    organization_id: UUID
    area_id: UUID
    action: str  # "granted", "revoked", "extended", "expired"
    timestamp: datetime
    performed_by: Optional[UUID] = None
    reason: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class UserInfoDTO(BaseModel):
    """DTO for user information in document access context."""

    id: UUID
    name: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}


# Forward reference imports
from .document_area_dto import DocumentAreaResponseDTO

UserDocumentAccessDetailResponseDTO.model_rebuild()