"""Profile Folder Permission routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from uuid import UUID

from ...presentation.dependencies import get_profile_folder_permission_use_case
from ...application.dtos.profile_folder_permission_dto import (
    ProfileFolderPermissionCreateDTO,
    ProfileFolderPermissionUpdateDTO,
    ProfileFolderPermissionResponseDTO,
    ProfileFolderPermissionDetailResponseDTO,
    ProfileFolderPermissionListResponseDTO,
    ProfileFolderPermissionStatsDTO,
    ProfileFolderPermissionFilterDTO,
    ProfileFolderPermissionBulkActionDTO,
    ProfileFolderPermissionBulkActionResponseDTO,
    ProfileFolderPermissionValidationDTO,
    ProfileFolderPermissionValidationResponseDTO,
    UserFolderAccessDTO,
    UserFolderAccessResponseDTO,
    FolderPermissionMatrixDTO,
    FolderPermissionMatrixResponseDTO,
)
from ...application.use_cases.profile_folder_permission_use_cases import ProfileFolderPermissionUseCase
from ...domain.value_objects.folder_permission_level import FolderPermissionLevel

router = APIRouter(tags=["Profile Folder Permissions"])


@router.post("/", response_model=ProfileFolderPermissionResponseDTO, status_code=status.HTTP_201_CREATED)
def create_profile_folder_permission(
    dto: ProfileFolderPermissionCreateDTO,
    use_case: ProfileFolderPermissionUseCase = Depends(get_profile_folder_permission_use_case),
):
    """Create a new profile folder permission."""
    try:
        return use_case.create_permission(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{permission_id}", response_model=ProfileFolderPermissionDetailResponseDTO)
def get_profile_folder_permission(
    permission_id: UUID,
    use_case: ProfileFolderPermissionUseCase = Depends(get_profile_folder_permission_use_case),
):
    """Get profile folder permission by ID with full details."""
    try:
        permission = use_case.get_permission_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found",
            )
        return permission
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{permission_id}", response_model=ProfileFolderPermissionResponseDTO)
def update_profile_folder_permission(
    permission_id: UUID,
    dto: ProfileFolderPermissionUpdateDTO,
    use_case: ProfileFolderPermissionUseCase = Depends(get_profile_folder_permission_use_case),
):
    """Update an existing profile folder permission."""
    try:
        permission = use_case.update_permission(permission_id, dto)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found",
            )
        return permission
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{permission_id}")
def delete_profile_folder_permission(
    permission_id: UUID,
    use_case: ProfileFolderPermissionUseCase = Depends(get_profile_folder_permission_use_case),
):
    """Delete a profile folder permission."""
    try:
        success = use_case.delete_permission(permission_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found",
            )
        return {"message": "Permission deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=ProfileFolderPermissionListResponseDTO)
def list_profile_folder_permissions(
    profile_id: Optional[UUID] = Query(None, description="Filter by profile ID"),
    folder_path: Optional[str] = Query(None, description="Filter by folder path"),
    folder_path_prefix: Optional[str] = Query(None, description="Filter by folder path prefix"),
    permission_level: Optional[FolderPermissionLevel] = Query(None, description="Filter by permission level"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    created_by: Optional[UUID] = Query(None, description="Filter by creator"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_root_folder: Optional[bool] = Query(None, description="Filter root folder permissions"),
    min_folder_depth: Optional[int] = Query(None, description="Filter by minimum folder depth"),
    max_folder_depth: Optional[int] = Query(None, description="Filter by maximum folder depth"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    use_case: ProfileFolderPermissionUseCase = Depends(get_profile_folder_permission_use_case),
):
    """List profile folder permissions with filtering and pagination."""
    try:
        filters = ProfileFolderPermissionFilterDTO(
            profile_id=profile_id,
            folder_path=folder_path,
            folder_path_prefix=folder_path_prefix,
            permission_level=permission_level,
            organization_id=organization_id,
            created_by=created_by,
            is_active=is_active,
            is_root_folder=is_root_folder,
            min_folder_depth=min_folder_depth,
            max_folder_depth=max_folder_depth,
        )
        return use_case.list_permissions(filters, page, page_size)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stats", response_model=ProfileFolderPermissionStatsDTO)
def get_profile_folder_permission_stats(
    organization_id: UUID = Query(..., description="Organization ID"),
    use_case: ProfileFolderPermissionUseCase = Depends(get_profile_folder_permission_use_case),
):
    """Get profile folder permission statistics."""
    try:
        return use_case.get_permission_stats(organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/validate", response_model=ProfileFolderPermissionValidationResponseDTO)
def validate_profile_folder_permission(
    dto: ProfileFolderPermissionValidationDTO,
    use_case: ProfileFolderPermissionUseCase = Depends(get_profile_folder_permission_use_case),
):
    """Validate a profile folder permission."""
    try:
        return use_case.validate_permission(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk-action", response_model=ProfileFolderPermissionBulkActionResponseDTO)
def bulk_action_profile_folder_permissions(
    dto: ProfileFolderPermissionBulkActionDTO,
    use_case: ProfileFolderPermissionUseCase = Depends(get_profile_folder_permission_use_case),
):
    """Perform bulk action on profile folder permissions."""
    try:
        return use_case.bulk_action(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/check-access", response_model=UserFolderAccessResponseDTO)
def check_user_folder_access(
    dto: UserFolderAccessDTO,
    use_case: ProfileFolderPermissionUseCase = Depends(get_profile_folder_permission_use_case),
):
    """Check if a user can access a specific folder."""
    try:
        return use_case.check_user_folder_access(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/matrix", response_model=FolderPermissionMatrixResponseDTO)
def get_folder_permission_matrix(
    organization_id: UUID = Query(..., description="Organization ID"),
    folder_paths: Optional[str] = Query(None, description="Comma-separated folder paths"),
    profile_ids: Optional[str] = Query(None, description="Comma-separated profile IDs"),
    include_inactive: bool = Query(False, description="Include inactive permissions"),
    use_case: ProfileFolderPermissionUseCase = Depends(get_profile_folder_permission_use_case),
):
    """Get folder permission matrix for an organization."""
    try:
        # Parse comma-separated values
        folder_paths_list = None
        if folder_paths:
            folder_paths_list = [path.strip() for path in folder_paths.split(",") if path.strip()]
        
        profile_ids_list = None
        if profile_ids:
            profile_ids_list = [UUID(id.strip()) for id in profile_ids.split(",") if id.strip()]
        
        dto = FolderPermissionMatrixDTO(
            organization_id=organization_id,
            folder_paths=folder_paths_list,
            profile_ids=profile_ids_list,
            include_inactive=include_inactive,
        )
        return use_case.get_folder_permission_matrix(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid UUID format: {str(e)}")