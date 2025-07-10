"""User Document Access management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from uuid import UUID

from ..dependencies import get_user_document_access_use_case
from ...application.dtos.user_document_access_dto import (
    UserDocumentAccessCreateDTO,
    UserDocumentAccessUpdateDTO,
    UserDocumentAccessResponseDTO,
    UserDocumentAccessDetailResponseDTO,
    UserDocumentAccessListResponseDTO,
    UserDocumentAccessBatchCreateDTO,
    UserDocumentAccessBatchUpdateDTO,
    UserDocumentAccessTransferDTO,
    UserDocumentAccessStatsDTO,
    UserDocumentAccessFilterDTO,
    UserDocumentAccessSearchDTO,
    UserDocumentAccessBulkActionDTO,
    UserDocumentAccessBulkActionResponseDTO,
    UserDocumentAccessRevokeDTO,
    UserDocumentAccessExtendDTO,
    UserDocumentAccessAuditDTO,
)
from ...application.use_cases.user_document_access_use_cases import UserDocumentAccessUseCase

router = APIRouter(tags=["User Document Access"])


@router.post("/", response_model=UserDocumentAccessResponseDTO, status_code=status.HTTP_201_CREATED)
def create_user_document_access(
    dto: UserDocumentAccessCreateDTO,
    use_case: UserDocumentAccessUseCase = Depends(get_user_document_access_use_case),
):
    """Create a new user document access."""
    try:
        return use_case.create_access(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{access_id}", response_model=UserDocumentAccessDetailResponseDTO)
def get_user_document_access(
    access_id: UUID,
    use_case: UserDocumentAccessUseCase = Depends(get_user_document_access_use_case),
):
    """Get user document access by ID with full details."""
    try:
        access = use_case.get_access_by_id(access_id)
        if not access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User document access not found",
            )
        return access
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=UserDocumentAccessListResponseDTO)
def list_user_document_accesses(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    area_id: Optional[UUID] = Query(None, description="Filter by area ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_expired: Optional[bool] = Query(None, description="Filter by expiration status"),
    granted_by: Optional[UUID] = Query(None, description="Filter by granting user"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    use_case: UserDocumentAccessUseCase = Depends(get_user_document_access_use_case),
):
    """List user document accesses with filtering and pagination."""
    try:
        filters = UserDocumentAccessFilterDTO(
            user_id=user_id,
            organization_id=organization_id,
            area_id=area_id,
            is_active=is_active,
            is_expired=is_expired,
            granted_by=granted_by,
        )
        return use_case.list_accesses(filters, page, page_size)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{access_id}", response_model=UserDocumentAccessResponseDTO)
def update_user_document_access(
    access_id: UUID,
    dto: UserDocumentAccessUpdateDTO,
    use_case: UserDocumentAccessUseCase = Depends(get_user_document_access_use_case),
):
    """Update user document access information."""
    try:
        updated_access = use_case.update_access(access_id, dto)
        if not updated_access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User document access not found",
            )
        return updated_access
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{access_id}")
def delete_user_document_access(
    access_id: UUID,
    use_case: UserDocumentAccessUseCase = Depends(get_user_document_access_use_case),
):
    """Delete user document access."""
    try:
        success = use_case.delete_access(access_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User document access not found",
            )
        return {"message": "User document access deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/revoke")
def revoke_user_document_access(
    dto: UserDocumentAccessRevokeDTO,
    use_case: UserDocumentAccessUseCase = Depends(get_user_document_access_use_case),
):
    """Revoke user document access."""
    try:
        success = use_case.revoke_access(dto)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User document access not found or already revoked",
            )
        return {"message": "User document access revoked successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{access_id}/extend", response_model=UserDocumentAccessResponseDTO)
def extend_user_document_access(
    access_id: UUID,
    dto: UserDocumentAccessExtendDTO,
    use_case: UserDocumentAccessUseCase = Depends(get_user_document_access_use_case),
):
    """Extend user document access expiration."""
    try:
        extended_access = use_case.extend_access(access_id, dto)
        if not extended_access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User document access not found",
            )
        return extended_access
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/batch", response_model=List[UserDocumentAccessResponseDTO])
def batch_create_user_document_accesses(
    dto: UserDocumentAccessBatchCreateDTO,
    use_case: UserDocumentAccessUseCase = Depends(get_user_document_access_use_case),
):
    """Create multiple user document accesses."""
    try:
        return use_case.batch_create_accesses(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/transfer", response_model=List[UserDocumentAccessResponseDTO])
def transfer_user_document_accesses(
    dto: UserDocumentAccessTransferDTO,
    use_case: UserDocumentAccessUseCase = Depends(get_user_document_access_use_case),
):
    """Transfer user accesses from one area to another."""
    try:
        return use_case.transfer_accesses(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk-action", response_model=UserDocumentAccessBulkActionResponseDTO)
def bulk_action_user_document_accesses(
    dto: UserDocumentAccessBulkActionDTO,
    use_case: UserDocumentAccessUseCase = Depends(get_user_document_access_use_case),
):
    """Perform bulk action on user document accesses."""
    try:
        return use_case.bulk_action(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stats", response_model=UserDocumentAccessStatsDTO)
def get_user_document_access_stats(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    use_case: UserDocumentAccessUseCase = Depends(get_user_document_access_use_case),
):
    """Get user document access statistics."""
    try:
        return use_case.get_access_stats(organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))