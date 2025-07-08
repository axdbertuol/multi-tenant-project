from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class UserFunctionAreaCreateDTO(BaseModel):
    """DTO for creating a new user function area assignment."""

    user_id: UUID = Field(..., description="User ID")
    organization_id: UUID = Field(..., description="Organization ID")
    function_id: UUID = Field(..., description="Management function ID")
    area_id: UUID = Field(..., description="Document area ID")
    assigned_by: UUID = Field(..., description="ID of user making the assignment")


class UserFunctionAreaUpdateDTO(BaseModel):
    """DTO for updating an existing user function area assignment."""

    function_id: Optional[UUID] = Field(None, description="New management function ID")
    area_id: Optional[UUID] = Field(None, description="New document area ID")
    is_active: Optional[bool] = Field(None, description="Active status")


class UserFunctionAreaBatchCreateDTO(BaseModel):
    """DTO for creating multiple user function area assignments."""

    assignments: List[UserFunctionAreaCreateDTO] = Field(
        ..., description="List of assignments to create"
    )


class UserFunctionAreaBatchUpdateDTO(BaseModel):
    """DTO for batch updating user function area assignments."""

    assignment_ids: List[UUID] = Field(..., description="Assignment IDs to update")
    function_id: Optional[UUID] = Field(None, description="New management function ID")
    area_id: Optional[UUID] = Field(None, description="New document area ID")
    is_active: Optional[bool] = Field(None, description="Active status")


class UserFunctionAreaTransferDTO(BaseModel):
    """DTO for transferring user assignments between functions/areas."""

    source_function_id: UUID = Field(..., description="Source function ID")
    target_function_id: UUID = Field(..., description="Target function ID")
    source_area_id: Optional[UUID] = Field(None, description="Source area ID")
    target_area_id: Optional[UUID] = Field(None, description="Target area ID")
    user_ids: List[UUID] = Field(..., description="User IDs to transfer")
    transferred_by: UUID = Field(..., description="ID of user making the transfer")


class UserFunctionAreaResponseDTO(BaseModel):
    """DTO for user function area assignment response data."""

    id: UUID
    user_id: UUID
    organization_id: UUID
    function_id: UUID
    area_id: UUID
    assigned_by: UUID
    assigned_at: datetime
    is_active: bool
    
    # Related data
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    function_name: Optional[str] = None
    area_name: Optional[str] = None
    area_folder_path: Optional[str] = None
    assigned_by_name: Optional[str] = None

    model_config = {"from_attributes": True}


class UserFunctionAreaDetailResponseDTO(UserFunctionAreaResponseDTO):
    """DTO for detailed user function area assignment response."""

    function: "ManagementFunctionResponseDTO"
    area: "DocumentAreaResponseDTO"
    user: "UserResponseDTO"
    assigned_by_user: "UserResponseDTO"
    accessible_folders: List[str]
    effective_permissions: List[str]


class UserFunctionAreaListResponseDTO(BaseModel):
    """DTO for paginated user function area assignment list response."""

    assignments: List[UserFunctionAreaResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserFunctionAreaStatsDTO(BaseModel):
    """DTO for user function area assignment statistics."""

    total_assignments: int
    active_assignments: int
    inactive_assignments: int
    assignments_by_function: dict[str, int]
    assignments_by_area: dict[str, int]
    assignments_by_user: dict[str, int]
    recent_assignments: List[UserFunctionAreaResponseDTO]


class UserFunctionAreaFilterDTO(BaseModel):
    """DTO for filtering user function area assignments."""

    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    organization_id: Optional[UUID] = Field(None, description="Filter by organization ID")
    function_id: Optional[UUID] = Field(None, description="Filter by function ID")
    area_id: Optional[UUID] = Field(None, description="Filter by area ID")
    assigned_by: Optional[UUID] = Field(None, description="Filter by assigned by user")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    assigned_after: Optional[datetime] = Field(None, description="Filter by assignment date")
    assigned_before: Optional[datetime] = Field(None, description="Filter by assignment date")


class UserFunctionAreaSearchDTO(BaseModel):
    """DTO for searching user function area assignments."""

    query: str = Field(..., min_length=1, description="Search query")
    search_fields: List[str] = Field(
        default_factory=lambda: ["user_email", "user_name", "function_name", "area_name"],
        description="Fields to search in"
    )
    filters: Optional[UserFunctionAreaFilterDTO] = Field(
        None, description="Additional filters"
    )


class UserFunctionAreaBulkActionDTO(BaseModel):
    """DTO for bulk actions on user function area assignments."""

    assignment_ids: List[UUID] = Field(..., description="Assignment IDs to act on")
    action: str = Field(..., description="Action to perform: activate, deactivate, delete")
    performed_by: UUID = Field(..., description="ID of user performing the action")


class UserFunctionAreaBulkActionResponseDTO(BaseModel):
    """DTO for bulk action response."""

    success_count: int
    failure_count: int
    errors: List[str] = Field(default_factory=list)
    affected_assignments: List[UUID]


class UserContextDTO(BaseModel):
    """DTO for user context with function and area information."""

    user_id: UUID
    organization_id: UUID
    function_id: UUID
    function_name: str
    area_id: UUID
    area_name: str
    area_folder_path: str
    effective_permissions: List[str]
    accessible_folders: List[str]
    is_active: bool


# Forward reference imports
from .management_function_dto import ManagementFunctionResponseDTO
from .document_area_dto import DocumentAreaResponseDTO  
from .user_dto import UserResponseDTO

UserFunctionAreaDetailResponseDTO.model_rebuild()