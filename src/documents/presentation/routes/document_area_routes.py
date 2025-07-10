"""Document Area management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from uuid import UUID

from ..dependencies import get_document_area_use_case
from ...application.dtos.document_area_dto import (
    DocumentAreaCreateDTO,
    DocumentAreaUpdateDTO,
    DocumentAreaResponseDTO,
    DocumentAreaDetailResponseDTO,
    DocumentAreaListResponseDTO,
    DocumentAreaMoveDTO,
    DocumentAreaAssignmentDTO,
    DocumentAreaStatsDTO,
    DocumentAreaAccessDTO,
    DocumentAreaAccessResponseDTO,
    DocumentAreaTreeResponseDTO,
    DocumentAreaHierarchyResponseDTO,
)
from ...application.use_cases.document_area_use_cases import DocumentAreaUseCase

router = APIRouter(tags=["Document Areas"])


@router.post("/", response_model=DocumentAreaResponseDTO, status_code=status.HTTP_201_CREATED)
def create_document_area(
    dto: DocumentAreaCreateDTO,
    created_by: UUID = Query(..., description="User ID creating the area"),
    use_case: DocumentAreaUseCase = Depends(get_document_area_use_case),
):
    """Create a new document area."""
    try:
        return use_case.create_area(dto, created_by)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{area_id}", response_model=DocumentAreaDetailResponseDTO)
def get_document_area(
    area_id: UUID,
    use_case: DocumentAreaUseCase = Depends(get_document_area_use_case),
):
    """Get document area by ID with full details."""
    try:
        area = use_case.get_area_by_id(area_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document area not found",
            )
        return area
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=DocumentAreaListResponseDTO)
def list_document_areas(
    organization_id: UUID = Query(..., description="Organization ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_system: bool = Query(True, description="Include system areas"),
    use_case: DocumentAreaUseCase = Depends(get_document_area_use_case),
):
    """List document areas with pagination."""
    try:
        return use_case.list_areas(
            organization_id=organization_id,
            page=page,
            page_size=page_size,
            include_system=include_system,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{area_id}", response_model=DocumentAreaResponseDTO)
def update_document_area(
    area_id: UUID,
    dto: DocumentAreaUpdateDTO,
    updated_by: UUID = Query(..., description="User ID updating the area"),
    use_case: DocumentAreaUseCase = Depends(get_document_area_use_case),
):
    """Update document area information."""
    try:
        updated_area = use_case.update_area(area_id, dto, updated_by)
        if not updated_area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document area not found",
            )
        return updated_area
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{area_id}")
def delete_document_area(
    area_id: UUID,
    deleted_by: UUID = Query(..., description="User ID deleting the area"),
    use_case: DocumentAreaUseCase = Depends(get_document_area_use_case),
):
    """Delete document area (soft delete)."""
    try:
        success = use_case.delete_area(area_id, deleted_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document area not found",
            )
        return {"message": "Document area deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{area_id}/move", response_model=DocumentAreaResponseDTO)
def move_document_area(
    area_id: UUID,
    dto: DocumentAreaMoveDTO,
    moved_by: UUID = Query(..., description="User ID moving the area"),
    use_case: DocumentAreaUseCase = Depends(get_document_area_use_case),
):
    """Move document area to a new parent."""
    try:
        moved_area = use_case.move_area(area_id, dto, moved_by)
        if not moved_area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document area not found",
            )
        return moved_area
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/assign", status_code=status.HTTP_201_CREATED)
def assign_area_to_user(
    dto: DocumentAreaAssignmentDTO,
    use_case: DocumentAreaUseCase = Depends(get_document_area_use_case),
):
    """Assign document area to a user."""
    try:
        success = use_case.assign_area_to_user(dto)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to assign area to user",
            )
        return {"message": "Area assigned to user successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organization/{organization_id}/hierarchy", response_model=DocumentAreaHierarchyResponseDTO)
def get_area_hierarchy(
    organization_id: UUID,
    use_case: DocumentAreaUseCase = Depends(get_document_area_use_case),
):
    """Get document area hierarchy for an organization."""
    try:
        return use_case.get_area_hierarchy(organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organization/{organization_id}/tree", response_model=List[DocumentAreaTreeResponseDTO])
def get_area_tree(
    organization_id: UUID,
    use_case: DocumentAreaUseCase = Depends(get_document_area_use_case),
):
    """Get document area hierarchy as tree structure."""
    try:
        return use_case.get_area_tree(organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/access/check", response_model=DocumentAreaAccessResponseDTO)
def check_area_access(
    dto: DocumentAreaAccessDTO,
    use_case: DocumentAreaUseCase = Depends(get_document_area_use_case),
):
    """Check if a user has access to a specific folder through areas."""
    try:
        return use_case.check_area_access(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organization/{organization_id}/stats", response_model=DocumentAreaStatsDTO)
def get_area_stats(
    organization_id: UUID,
    use_case: DocumentAreaUseCase = Depends(get_document_area_use_case),
):
    """Get document area statistics for an organization."""
    try:
        return use_case.get_area_stats(organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/organization/{organization_id}/default", response_model=List[DocumentAreaResponseDTO])
def create_default_areas(
    organization_id: UUID,
    use_case: DocumentAreaUseCase = Depends(get_document_area_use_case),
):
    """Create default document areas for an organization."""
    try:
        return use_case.create_default_areas(organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))