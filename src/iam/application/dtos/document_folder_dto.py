from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class DocumentFolderCreateDTO(BaseModel):
    """DTO for creating a new document folder."""

    name: str = Field(..., min_length=1, max_length=255, description="Folder name")
    path: str = Field(..., description="Full folder path")
    organization_id: UUID = Field(..., description="Organization ID")
    area_id: UUID = Field(..., description="Document area ID")
    parent_folder_id: Optional[UUID] = Field(
        None, description="Parent folder ID for hierarchical structure"
    )
    is_virtual: bool = Field(False, description="Whether this is a virtual folder")
    metadata: Optional[dict] = Field(None, description="Additional folder metadata")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Folder name cannot be empty")
        # Remove leading/trailing spaces and invalid characters
        name = v.strip()
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in invalid_chars:
            if char in name:
                raise ValueError(f"Folder name cannot contain '{char}'")
        return name

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Folder path cannot be empty")
        # Ensure path starts with / but doesn't end with / (unless root)
        path = v.strip()
        if not path.startswith("/"):
            path = "/" + path
        if path.endswith("/") and path != "/":
            path = path[:-1]
        return path


class DocumentFolderUpdateDTO(BaseModel):
    """DTO for updating an existing document folder."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Folder name"
    )
    area_id: Optional[UUID] = Field(
        None, description="Document area ID"
    )
    parent_folder_id: Optional[UUID] = Field(
        None, description="Parent folder ID"
    )
    is_virtual: Optional[bool] = Field(
        None, description="Whether this is a virtual folder"
    )
    metadata: Optional[dict] = Field(
        None, description="Additional folder metadata"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Folder name cannot be empty")
        # Remove leading/trailing spaces and invalid characters
        name = v.strip()
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in invalid_chars:
            if char in name:
                raise ValueError(f"Folder name cannot contain '{char}'")
        return name


class DocumentFolderMoveDTO(BaseModel):
    """DTO for moving a document folder to a new parent or area."""

    new_parent_id: Optional[UUID] = Field(
        None, description="New parent folder ID (None for root level)"
    )
    new_area_id: Optional[UUID] = Field(
        None, description="New document area ID"
    )


class DocumentFolderBatchCreateDTO(BaseModel):
    """DTO for creating multiple document folders."""

    folders: List[DocumentFolderCreateDTO] = Field(
        ..., description="List of folders to create"
    )


class DocumentFolderResponseDTO(BaseModel):
    """DTO for document folder response data."""

    id: UUID
    name: str
    path: str
    organization_id: UUID
    area_id: UUID
    parent_folder_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    is_virtual: bool
    metadata: Optional[dict] = None
    
    # Calculated fields
    has_children: bool = False
    child_count: int = 0
    file_count: int = 0
    total_size: int = 0
    depth_level: int = 0
    
    # Related data
    area_name: Optional[str] = None
    parent_folder_name: Optional[str] = None

    model_config = {"from_attributes": True}


class DocumentFolderDetailResponseDTO(DocumentFolderResponseDTO):
    """DTO for detailed document folder response with children and permissions."""

    children: List["DocumentFolderResponseDTO"]
    area: "DocumentAreaResponseDTO"
    parent_folder: Optional["DocumentFolderResponseDTO"] = None
    accessible_by_users: List[UUID]
    access_permissions: List[str]


class DocumentFolderTreeResponseDTO(BaseModel):
    """DTO for document folder tree structure."""

    folder: DocumentFolderResponseDTO
    children: List["DocumentFolderTreeResponseDTO"]
    permissions: List[str]


class DocumentFolderListResponseDTO(BaseModel):
    """DTO for paginated document folder list response."""

    folders: List[DocumentFolderResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentFolderStatsDTO(BaseModel):
    """DTO for document folder statistics."""

    total_folders: int
    active_folders: int
    virtual_folders: int
    physical_folders: int
    root_folders: int
    folders_by_area: dict[str, int]
    folders_by_level: dict[int, int]
    total_files: int
    total_size: int


class DocumentFolderAccessDTO(BaseModel):
    """DTO for checking document folder access."""

    user_id: UUID = Field(..., description="User ID")
    folder_path: str = Field(..., description="Folder path to check")
    organization_id: UUID = Field(..., description="Organization ID")
    action: str = Field(default="read", description="Action to check: read, write, delete")


class DocumentFolderAccessResponseDTO(BaseModel):
    """DTO for document folder access response."""

    has_access: bool
    access_level: str  # "read", "write", "admin"
    accessible_folders: List[DocumentFolderResponseDTO]
    access_reason: str
    restrictions: List[str] = Field(default_factory=list)


class DocumentFolderFilterDTO(BaseModel):
    """DTO for filtering document folders."""

    organization_id: Optional[UUID] = Field(None, description="Filter by organization ID")
    area_id: Optional[UUID] = Field(None, description="Filter by area ID")
    parent_folder_id: Optional[UUID] = Field(None, description="Filter by parent folder ID")
    is_virtual: Optional[bool] = Field(None, description="Filter by virtual status")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    path_pattern: Optional[str] = Field(None, description="Filter by path pattern")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date")


class DocumentFolderSearchDTO(BaseModel):
    """DTO for searching document folders."""

    query: str = Field(..., min_length=1, description="Search query")
    search_fields: List[str] = Field(
        default_factory=lambda: ["name", "path", "area_name"],
        description="Fields to search in"
    )
    filters: Optional[DocumentFolderFilterDTO] = Field(
        None, description="Additional filters"
    )


class DocumentFolderBulkActionDTO(BaseModel):
    """DTO for bulk actions on document folders."""

    folder_ids: List[UUID] = Field(..., description="Folder IDs to act on")
    action: str = Field(..., description="Action to perform: activate, deactivate, delete, move")
    target_area_id: Optional[UUID] = Field(None, description="Target area ID for move action")
    target_parent_id: Optional[UUID] = Field(None, description="Target parent ID for move action")
    performed_by: UUID = Field(..., description="ID of user performing the action")


class DocumentFolderBulkActionResponseDTO(BaseModel):
    """DTO for bulk action response."""

    success_count: int
    failure_count: int
    errors: List[str] = Field(default_factory=list)
    affected_folders: List[UUID]


class DocumentFolderSyncDTO(BaseModel):
    """DTO for synchronizing document folders with file system."""

    organization_id: UUID = Field(..., description="Organization ID")
    area_id: UUID = Field(..., description="Area ID to sync")
    base_path: str = Field(..., description="Base file system path")
    sync_mode: str = Field(default="incremental", description="Sync mode: full, incremental")
    delete_orphaned: bool = Field(False, description="Delete folders not found in file system")


class DocumentFolderSyncResponseDTO(BaseModel):
    """DTO for folder synchronization response."""

    created_folders: int
    updated_folders: int
    deleted_folders: int
    errors: List[str] = Field(default_factory=list)
    sync_duration: float
    last_sync: datetime


# Forward reference imports
from .document_area_dto import DocumentAreaResponseDTO

DocumentFolderDetailResponseDTO.model_rebuild()
DocumentFolderTreeResponseDTO.model_rebuild()