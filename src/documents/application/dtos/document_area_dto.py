from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class DocumentAreaCreateDTO(BaseModel):
    """DTO for creating a new document area."""

    name: str = Field(..., min_length=2, max_length=50, description="Area name")
    description: str = Field(..., max_length=500, description="Area description")
    organization_id: UUID = Field(..., description="Organization ID")
    parent_area_id: Optional[UUID] = Field(
        None, description="Parent area ID for hierarchical structure"
    )
    folder_path: str = Field(..., description="Folder path for document access")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Area name cannot be empty")
        # Keep original casing for areas (unlike functions)
        return v.strip()

    @field_validator("folder_path")
    @classmethod
    def validate_folder_path(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Folder path cannot be empty")
        # Ensure path starts with / but doesn't end with /
        path = v.strip()
        if not path.startswith("/"):
            path = "/" + path
        if path.endswith("/") and path != "/":
            path = path[:-1]
        return path


class DocumentAreaUpdateDTO(BaseModel):
    """DTO for updating an existing document area."""

    name: Optional[str] = Field(
        None, min_length=2, max_length=50, description="Area name"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Area description"
    )
    folder_path: Optional[str] = Field(
        None, description="Folder path for document access"
    )
    parent_area_id: Optional[UUID] = Field(
        None, description="Parent area ID for hierarchical structure"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Area name cannot be empty")
        return v.strip()

    @field_validator("folder_path")
    @classmethod
    def validate_folder_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Folder path cannot be empty")
        # Ensure path starts with / but doesn't end with /
        path = v.strip()
        if not path.startswith("/"):
            path = "/" + path
        if path.endswith("/") and path != "/":
            path = path[:-1]
        return path


class DocumentAreaMoveDTO(BaseModel):
    """DTO for moving a document area to a new parent."""

    new_parent_id: Optional[UUID] = Field(
        None, description="New parent area ID (None for root level)"
    )


class DocumentAreaAssignmentDTO(BaseModel):
    """DTO for assigning a document area to a user."""

    user_id: UUID = Field(..., description="User ID")
    assigned_by: UUID = Field(..., description="ID of user making the assignment")


class DocumentAreaResponseDTO(BaseModel):
    """DTO for document area response data."""

    id: UUID
    name: str
    description: str
    organization_id: UUID
    parent_area_id: Optional[UUID] = None
    folder_path: str
    created_at: datetime
    created_by: UUID
    is_active: bool
    is_system_area: bool = False
    assignment_count: int = 0
    subfolder_count: int = 0
    has_children: bool = False
    hierarchy_level: int = 0

    model_config = {"from_attributes": True}


class DocumentAreaDetailResponseDTO(DocumentAreaResponseDTO):
    """DTO for detailed document area response with assignments and hierarchy."""

    assignments: List["UserDocumentAccessResponseDTO"]
    children: List["DocumentAreaResponseDTO"]
    accessible_folders: List[str]
    parent_area: Optional["DocumentAreaResponseDTO"] = None


class DocumentAreaTreeResponseDTO(BaseModel):
    """DTO for document area tree structure."""

    area: DocumentAreaResponseDTO
    children: List["DocumentAreaTreeResponseDTO"]
    accessible_paths: List[str]


class DocumentAreaListResponseDTO(BaseModel):
    """DTO for paginated document area list response."""

    areas: List[DocumentAreaResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentAreaStatsDTO(BaseModel):
    """DTO for document area statistics."""

    total_areas: int
    active_areas: int
    root_areas: int
    system_areas: int
    custom_areas: int
    total_assignments: int
    areas_by_level: dict[int, int]
    folder_coverage: dict[str, int]


class DocumentAreaAccessDTO(BaseModel):
    """DTO for checking document area access."""

    user_id: UUID = Field(..., description="User ID")
    folder_path: str = Field(..., description="Folder path to check")
    organization_id: UUID = Field(..., description="Organization ID")


class DocumentAreaAccessResponseDTO(BaseModel):
    """DTO for document area access response."""

    has_access: bool
    accessible_areas: List[DocumentAreaResponseDTO]
    access_reason: str
    accessible_paths: List[str]


class DocumentAreaHierarchyResponseDTO(BaseModel):
    """DTO for document area hierarchy response."""

    areas: List[DocumentAreaResponseDTO]
    hierarchy_tree: dict
    validation_errors: List[str] = Field(default_factory=list)


# Forward reference imports
from .user_document_access_dto import UserDocumentAccessResponseDTO

DocumentAreaDetailResponseDTO.model_rebuild()
DocumentAreaTreeResponseDTO.model_rebuild()