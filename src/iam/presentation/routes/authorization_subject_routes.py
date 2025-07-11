from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from uuid import UUID

from ..dependencies import get_authorization_subject_use_case
from ..auth_dependencies import get_current_user_from_jwt
from ...application.use_cases.authorization_subject_use_cases import (
    AuthorizationSubjectUseCase,
)
from ...application.dtos.authorization_subject_dto import (
    AuthorizationSubjectCreateDTO,
    AuthorizationSubjectUpdateDTO,
    AuthorizationSubjectTransferOwnershipDTO,
    AuthorizationSubjectMoveOrganizationDTO,
    AuthorizationSubjectResponseDTO,
    AuthorizationSubjectListResponseDTO,
    AuthorizationSubjectFilterDTO,
    AuthorizationSubjectSearchDTO,
    BulkTransferOwnershipDTO,
    BulkMoveOrganizationDTO,
    BulkAuthorizationSubjectOperationDTO,
    BulkOperationResponseDTO,
    AuthorizationSubjectStatisticsDTO,
)

router = APIRouter(prefix="/authorization-subjects", tags=["Authorization Subjects"])


@router.post(
    "/",
    response_model=AuthorizationSubjectResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
def create_authorization_subject(
    dto: AuthorizationSubjectCreateDTO,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Create a new authorization subject."""
    try:
        return use_case.create_subject(dto, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{subject_id}", response_model=AuthorizationSubjectResponseDTO)
def get_authorization_subject(
    subject_id: UUID,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Get authorization subject by ID."""
    try:
        subject = use_case.get_subject_by_id(subject_id)
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authorization subject not found",
            )
        return subject
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{subject_id}", response_model=AuthorizationSubjectResponseDTO)
def update_authorization_subject(
    subject_id: UUID,
    dto: AuthorizationSubjectUpdateDTO,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Update an authorization subject."""
    try:
        return use_case.update_subject(subject_id, dto, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{subject_id}/transfer-ownership", response_model=AuthorizationSubjectResponseDTO
)
def transfer_ownership(
    subject_id: UUID,
    dto: AuthorizationSubjectTransferOwnershipDTO,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Transfer ownership of an authorization subject."""
    try:
        return use_case.transfer_ownership(subject_id, dto, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{subject_id}/move-organization", response_model=AuthorizationSubjectResponseDTO
)
def move_to_organization(
    subject_id: UUID,
    dto: AuthorizationSubjectMoveOrganizationDTO,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Move authorization subject to different organization."""
    try:
        return use_case.move_to_organization(subject_id, dto, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subject_id}/activate", response_model=AuthorizationSubjectResponseDTO)
def activate_subject(
    subject_id: UUID,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Activate an authorization subject."""
    try:
        return use_case.activate_subject(subject_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subject_id}/deactivate", response_model=AuthorizationSubjectResponseDTO)
def deactivate_subject(
    subject_id: UUID,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Deactivate an authorization subject."""
    try:
        return use_case.deactivate_subject(subject_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{subject_id}")
def delete_authorization_subject(
    subject_id: UUID,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Delete an authorization subject."""
    try:
        success = use_case.delete_subject(subject_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authorization subject not found",
            )
        return {"message": "Authorization subject deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=AuthorizationSubjectListResponseDTO)
def list_authorization_subjects(
    organization_id: Optional[UUID] = Query(
        None, description="Filter by organization ID"
    ),
    subject_type: Optional[str] = Query(None, description="Filter by subject type"),
    owner_id: Optional[UUID] = Query(None, description="Filter by owner ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """List authorization subjects with pagination and filters."""
    try:
        filters = AuthorizationSubjectFilterDTO(
            organization_id=organization_id,
            subject_type=subject_type,
            owner_id=owner_id,
            is_active=is_active,
            page=page,
            page_size=page_size,
        )
        return use_case.list_subjects(filters)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/search", response_model=AuthorizationSubjectResponseDTO)
def find_subject_by_reference(
    dto: AuthorizationSubjectSearchDTO,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Find authorization subject by external reference."""
    try:
        subject = use_case.find_subject_by_reference(dto)
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authorization subject not found",
            )
        return subject
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users/{user_id}", response_model=List[AuthorizationSubjectResponseDTO])
def get_user_subjects(
    user_id: UUID,
    organization_id: Optional[UUID] = Query(
        None, description="Filter by organization ID"
    ),
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Get all subjects owned by a user."""
    try:
        return use_case.get_user_subjects(user_id, organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/organizations/{organization_id}",
    response_model=List[AuthorizationSubjectResponseDTO],
)
def get_organization_subjects(
    organization_id: UUID,
    subject_type: Optional[str] = Query(None, description="Filter by subject type"),
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Get all subjects in an organization."""
    try:
        return use_case.get_organization_subjects(organization_id, subject_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/organizations/{organization_id}/active",
    response_model=List[AuthorizationSubjectResponseDTO],
)
def get_active_organization_subjects(
    organization_id: UUID,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Get all active subjects in an organization."""
    try:
        return use_case.get_active_organization_subjects(organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk/transfer-ownership", response_model=BulkOperationResponseDTO)
def bulk_transfer_ownership(
    dto: BulkTransferOwnershipDTO,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Bulk transfer ownership of multiple subjects."""
    try:
        return use_case.bulk_transfer_ownership(dto, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk/move-organization", response_model=BulkOperationResponseDTO)
def bulk_move_to_organization(
    dto: BulkMoveOrganizationDTO,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Bulk move subjects to different organization."""
    try:
        return use_case.bulk_move_to_organization(dto, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk/activate", response_model=BulkOperationResponseDTO)
def bulk_activate_subjects(
    dto: BulkAuthorizationSubjectOperationDTO,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Bulk activate multiple subjects."""
    try:
        return use_case.bulk_activate_subjects(dto, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk/deactivate", response_model=BulkOperationResponseDTO)
def bulk_deactivate_subjects(
    dto: BulkAuthorizationSubjectOperationDTO,
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Bulk deactivate multiple subjects."""
    try:
        return use_case.bulk_deactivate_subjects(dto, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/statistics", response_model=AuthorizationSubjectStatisticsDTO)
def get_subject_statistics(
    organization_id: Optional[UUID] = Query(
        None, description="Organization ID for scoped statistics"
    ),
    use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    current_user=Depends(get_current_user_from_jwt),
):
    """Get statistics about authorization subjects."""
    try:
        return use_case.get_subject_statistics(organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
