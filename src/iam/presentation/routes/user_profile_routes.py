"""User Profile assignment routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from uuid import UUID

from ...presentation.dependencies import get_user_profile_use_case
from ...application.dtos.user_profile_dto import (
    UserProfileCreateDTO,
    UserProfileUpdateDTO,
    UserProfileExtendDTO,
    UserProfileRevokeDTO,
    UserProfileResponseDTO,
    UserProfileDetailResponseDTO,
    UserProfileListResponseDTO,
    UserProfileStatsDTO,
    UserProfileFilterDTO,
    UserProfileBulkActionDTO,
    UserProfileBulkActionResponseDTO,
    UserProfileBatchCreateDTO,
    UserProfileBatchCreateResponseDTO,
    UserProfileTransferDTO,
    UserProfileTransferResponseDTO,
    UserProfileHistoryDTO,
    UserProfileHistoryResponseDTO,
    UserContextDTO,
)
from ...application.use_cases.user_profile_use_cases import UserProfileUseCase

router = APIRouter(tags=["User Profiles"])


@router.post("/", response_model=UserProfileResponseDTO, status_code=status.HTTP_201_CREATED)
def create_user_profile_assignment(
    dto: UserProfileCreateDTO,
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """Create a new user profile assignment (validates user belongs to organization)."""
    try:
        return use_case.create_assignment(dto)
    except ValueError as e:
        if "organization" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to the profile's organization",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{assignment_id}", response_model=UserProfileDetailResponseDTO)
def get_user_profile_assignment(
    assignment_id: UUID,
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """Get user profile assignment by ID with full details."""
    try:
        assignment = use_case.get_assignment_by_id(assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
            )
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{assignment_id}", response_model=UserProfileResponseDTO)
def update_user_profile_assignment(
    assignment_id: UUID,
    dto: UserProfileUpdateDTO,
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """Update an existing user profile assignment."""
    try:
        assignment = use_case.update_assignment(assignment_id, dto)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
            )
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{assignment_id}")
def delete_user_profile_assignment(
    assignment_id: UUID,
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """Delete a user profile assignment."""
    try:
        success = use_case.delete_assignment(assignment_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
            )
        return {"message": "Assignment deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{assignment_id}/extend", response_model=UserProfileResponseDTO)
def extend_user_profile_assignment(
    assignment_id: UUID,
    dto: UserProfileExtendDTO,
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """Extend user profile assignment expiration."""
    try:
        assignment = use_case.extend_assignment(assignment_id, dto)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
            )
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{assignment_id}/revoke", response_model=UserProfileResponseDTO)
def revoke_user_profile_assignment(
    assignment_id: UUID,
    dto: UserProfileRevokeDTO,
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """Revoke user profile assignment."""
    try:
        assignment = use_case.revoke_assignment(assignment_id, dto)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
            )
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=UserProfileListResponseDTO)
def list_user_profile_assignments(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    profile_id: Optional[UUID] = Query(None, description="Filter by profile ID"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    assigned_by: Optional[UUID] = Query(None, description="Filter by assigned by user"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_expired: Optional[bool] = Query(None, description="Filter by expiration status"),
    is_revoked: Optional[bool] = Query(None, description="Filter by revocation status"),
    assignment_type: Optional[str] = Query(None, description="Filter by assignment type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    expiring_within_days: Optional[int] = Query(None, description="Filter assignments expiring within N days"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """List user profile assignments with filtering and pagination."""
    try:
        filters = UserProfileFilterDTO(
            user_id=user_id,
            profile_id=profile_id,
            organization_id=organization_id,
            assigned_by=assigned_by,
            is_active=is_active,
            is_expired=is_expired,
            is_revoked=is_revoked,
            assignment_type=assignment_type,
            status=status,
            expiring_within_days=expiring_within_days,
        )
        return use_case.list_assignments(filters, page, page_size)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stats", response_model=UserProfileStatsDTO)
def get_user_profile_stats(
    organization_id: UUID = Query(..., description="Organization ID"),
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """Get user profile assignment statistics."""
    try:
        return use_case.get_assignment_stats(organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/batch", response_model=UserProfileBatchCreateResponseDTO)
def batch_create_user_profile_assignments(
    dto: UserProfileBatchCreateDTO,
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """Create multiple user profile assignments."""
    try:
        return use_case.batch_create_assignments(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk-action", response_model=UserProfileBulkActionResponseDTO)
def bulk_action_user_profile_assignments(
    dto: UserProfileBulkActionDTO,
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """Perform bulk action on user profile assignments."""
    try:
        return use_case.bulk_action(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/transfer", response_model=UserProfileTransferResponseDTO)
def transfer_user_profile_assignments(
    dto: UserProfileTransferDTO,
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """Transfer user assignments from one profile to another."""
    try:
        return use_case.transfer_assignments(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/history", response_model=UserProfileHistoryResponseDTO)
def get_user_profile_history(
    user_id: UUID = Query(..., description="User ID"),
    profile_id: UUID = Query(..., description="Profile ID"),
    organization_id: UUID = Query(..., description="Organization ID"),
    include_revoked: bool = Query(True, description="Include revoked assignments"),
    include_expired: bool = Query(True, description="Include expired assignments"),
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """Get assignment history for a user and profile."""
    try:
        dto = UserProfileHistoryDTO(
            user_id=user_id,
            profile_id=profile_id,
            organization_id=organization_id,
            include_revoked=include_revoked,
            include_expired=include_expired,
        )
        return use_case.get_assignment_history(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users/{user_id}/context", response_model=UserContextDTO)
def get_user_context(
    user_id: UUID,
    organization_id: UUID = Query(..., description="Organization ID"),
    use_case: UserProfileUseCase = Depends(get_user_profile_use_case),
):
    """Get user context with all profile information."""
    try:
        return use_case.get_user_context(user_id, organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))