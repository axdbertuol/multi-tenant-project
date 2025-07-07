from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class AuthorizationSubjectCreateDTO(BaseModel):
    """DTO for creating a new authorization subject."""

    subject_type: str = Field(..., min_length=1, max_length=50, description="Type of the subject")
    subject_id: UUID = Field(..., description="External ID of the subject")
    owner_id: UUID = Field(..., description="ID of the owner user")
    organization_id: Optional[UUID] = Field(None, description="Organization ID (optional for global subjects)")
    is_active: bool = Field(default=True, description="Whether the subject is active")


class AuthorizationSubjectUpdateDTO(BaseModel):
    """DTO for updating an authorization subject."""

    is_active: Optional[bool] = Field(None, description="Whether the subject is active")


class AuthorizationSubjectTransferOwnershipDTO(BaseModel):
    """DTO for transferring ownership of an authorization subject."""

    new_owner_id: UUID = Field(..., description="ID of the new owner")


class AuthorizationSubjectMoveOrganizationDTO(BaseModel):
    """DTO for moving subject to different organization."""

    organization_id: Optional[UUID] = Field(None, description="Target organization ID (null for global)")


class AuthorizationSubjectResponseDTO(BaseModel):
    """DTO for authorization subject response."""

    id: UUID = Field(..., description="Subject ID")
    subject_type: str = Field(..., description="Type of the subject")
    subject_id: UUID = Field(..., description="External ID of the subject")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    owner_id: UUID = Field(..., description="Owner user ID")
    is_active: bool = Field(..., description="Whether the subject is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    subject_identifier: str = Field(..., description="Unique identifier for the subject")
    display_name: str = Field(..., description="Human-readable display name")
    is_global: bool = Field(..., description="Whether this is a global subject")


class AuthorizationSubjectListResponseDTO(BaseModel):
    """DTO for paginated list of authorization subjects."""

    subjects: List[AuthorizationSubjectResponseDTO] = Field(..., description="List of subjects")
    total: int = Field(..., description="Total number of subjects")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class BulkAuthorizationSubjectOperationDTO(BaseModel):
    """DTO for bulk operations on authorization subjects."""

    subject_ids: List[UUID] = Field(..., min_items=1, description="List of subject IDs")


class BulkTransferOwnershipDTO(BulkAuthorizationSubjectOperationDTO):
    """DTO for bulk ownership transfer."""

    new_owner_id: UUID = Field(..., description="ID of the new owner")


class BulkMoveOrganizationDTO(BulkAuthorizationSubjectOperationDTO):
    """DTO for bulk organization move."""

    organization_id: Optional[UUID] = Field(None, description="Target organization ID")


class BulkOperationResponseDTO(BaseModel):
    """DTO for bulk operation response."""

    updated_count: int = Field(..., description="Number of subjects updated")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    total_requested: int = Field(..., description="Total number of subjects requested for update")
    success_rate: float = Field(..., description="Success rate (0.0 to 1.0)")


class AuthorizationSubjectStatisticsDTO(BaseModel):
    """DTO for authorization subject statistics."""

    total_subjects: int = Field(..., description="Total number of subjects")
    active_subjects: int = Field(..., description="Number of active subjects")
    inactive_subjects: int = Field(..., description="Number of inactive subjects")
    subjects_by_type: Dict[str, int] = Field(..., description="Count of subjects by type")
    organization_id: Optional[str] = Field(None, description="Organization ID (if scoped)")


class AuthorizationSubjectFilterDTO(BaseModel):
    """DTO for filtering authorization subjects."""

    organization_id: Optional[UUID] = Field(None, description="Filter by organization ID")
    subject_type: Optional[str] = Field(None, description="Filter by subject type")
    owner_id: Optional[UUID] = Field(None, description="Filter by owner ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class AuthorizationSubjectSearchDTO(BaseModel):
    """DTO for searching authorization subjects by external reference."""

    subject_type: str = Field(..., description="Type of the subject")
    subject_id: UUID = Field(..., description="External ID of the subject")
    organization_id: Optional[UUID] = Field(None, description="Organization ID to search within")


# Conversion utilities
def entity_to_response_dto(subject) -> AuthorizationSubjectResponseDTO:
    """Convert AuthorizationSubject entity to response DTO."""
    return AuthorizationSubjectResponseDTO(
        id=subject.id,
        subject_type=subject.subject_type,
        subject_id=subject.subject_id,
        organization_id=subject.organization_id,
        owner_id=subject.owner_id,
        is_active=subject.is_active,
        created_at=subject.created_at,
        updated_at=subject.updated_at,
        subject_identifier=subject.get_subject_identifier(),
        display_name=subject.get_display_name(),
        is_global=subject.is_global_subject(),
    )


def entities_to_list_response_dto(
    subjects: List, total: int, page: int, page_size: int
) -> AuthorizationSubjectListResponseDTO:
    """Convert list of entities to paginated list response DTO."""
    total_pages = (total + page_size - 1) // page_size
    
    return AuthorizationSubjectListResponseDTO(
        subjects=[entity_to_response_dto(subject) for subject in subjects],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


def bulk_result_to_response_dto(
    result: Dict[str, Any], total_requested: int
) -> BulkOperationResponseDTO:
    """Convert bulk operation result to response DTO."""
    updated_count = result.get("updated_count", 0)
    errors = result.get("errors", [])
    success_rate = updated_count / total_requested if total_requested > 0 else 0.0
    
    return BulkOperationResponseDTO(
        updated_count=updated_count,
        errors=errors,
        total_requested=total_requested,
        success_rate=success_rate,
    )