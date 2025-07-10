"""Profile management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from uuid import UUID

from ...presentation.dependencies import get_profile_use_case
from ...application.dtos.profile_dto import (
    ProfileCreateDTO,
    ProfileUpdateDTO,
    ProfileResponseDTO,
    ProfileDetailResponseDTO,
    ProfileListResponseDTO,
    ProfileStatsDTO,
    ProfileFilterDTO,
    ProfileBulkActionDTO,
    ProfileBulkActionResponseDTO,
    ProfileValidationDTO,
    ProfileValidationResponseDTO,
    ProfileCloneDTO,
    ProfileCloneResponseDTO,
    ProfileUsageStatsDTO,
)
from ...application.use_cases.profile_use_cases import ProfileUseCase

router = APIRouter(tags=["Profiles"])


@router.post("/", response_model=ProfileResponseDTO, status_code=status.HTTP_201_CREATED)
def create_profile(
    dto: ProfileCreateDTO,
    use_case: ProfileUseCase = Depends(get_profile_use_case),
):
    """Create a new profile."""
    try:
        return use_case.create_profile(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{profile_id}", response_model=ProfileDetailResponseDTO)
def get_profile(
    profile_id: UUID,
    use_case: ProfileUseCase = Depends(get_profile_use_case),
):
    """Get profile by ID with full details."""
    try:
        profile = use_case.get_profile_by_id(profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )
        return profile
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{profile_id}", response_model=ProfileResponseDTO)
def update_profile(
    profile_id: UUID,
    dto: ProfileUpdateDTO,
    use_case: ProfileUseCase = Depends(get_profile_use_case),
):
    """Update an existing profile."""
    try:
        profile = use_case.update_profile(profile_id, dto)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )
        return profile
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{profile_id}")
def delete_profile(
    profile_id: UUID,
    use_case: ProfileUseCase = Depends(get_profile_use_case),
):
    """Delete a profile."""
    try:
        success = use_case.delete_profile(profile_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )
        return {"message": "Profile deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=ProfileListResponseDTO)
def list_profiles(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_by: Optional[UUID] = Query(None, description="Filter by creator"),
    is_system_profile: Optional[bool] = Query(None, description="Filter by system profile"),
    name: Optional[str] = Query(None, description="Filter by name pattern"),
    has_users: Optional[bool] = Query(None, description="Filter by having users"),
    has_permissions: Optional[bool] = Query(None, description="Filter by having permissions"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    use_case: ProfileUseCase = Depends(get_profile_use_case),
):
    """List profiles with filtering and pagination."""
    try:
        filters = ProfileFilterDTO(
            organization_id=organization_id,
            is_active=is_active,
            created_by=created_by,
            is_system_profile=is_system_profile,
            name=name,
            has_users=has_users,
            has_permissions=has_permissions,
        )
        return use_case.list_profiles(filters, page, page_size)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stats", response_model=ProfileStatsDTO)
def get_profile_stats(
    organization_id: UUID = Query(..., description="Organization ID"),
    use_case: ProfileUseCase = Depends(get_profile_use_case),
):
    """Get profile statistics for an organization."""
    try:
        return use_case.get_profile_stats(organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/validate", response_model=ProfileValidationResponseDTO)
def validate_profile(
    dto: ProfileValidationDTO,
    use_case: ProfileUseCase = Depends(get_profile_use_case),
):
    """Validate a profile."""
    try:
        return use_case.validate_profile(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/clone", response_model=ProfileCloneResponseDTO)
def clone_profile(
    dto: ProfileCloneDTO,
    use_case: ProfileUseCase = Depends(get_profile_use_case),
):
    """Clone a profile."""
    try:
        return use_case.clone_profile(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{profile_id}/usage-stats", response_model=ProfileUsageStatsDTO)
def get_profile_usage_stats(
    profile_id: UUID,
    use_case: ProfileUseCase = Depends(get_profile_use_case),
):
    """Get usage statistics for a profile."""
    try:
        return use_case.get_profile_usage_stats(profile_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk-action", response_model=ProfileBulkActionResponseDTO)
def bulk_action_profiles(
    dto: ProfileBulkActionDTO,
    use_case: ProfileUseCase = Depends(get_profile_use_case),
):
    """Perform bulk action on profiles."""
    try:
        return use_case.bulk_action(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))