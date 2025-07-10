"""Document Folder management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from uuid import UUID

from ..dependencies import get_document_folder_use_case
from ...application.dtos.document_folder_dto import (
    DocumentFolderCreateDTO,
    DocumentFolderUpdateDTO,
    DocumentFolderResponseDTO,
    DocumentFolderDetailResponseDTO,
    DocumentFolderListResponseDTO,
    DocumentFolderMoveDTO,
    DocumentFolderStatsDTO,
    DocumentFolderSearchDTO,
    DocumentFolderTreeResponseDTO,
    DocumentFolderAccessCheckDTO,
    DocumentFolderAccessCheckResponseDTO,
    DocumentFolderBulkActionDTO,
    DocumentFolderBulkActionResponseDTO,
)
from ...application.use_cases.document_folder_use_cases import DocumentFolderUseCase

router = APIRouter(tags=["Document Folders"])


@router.post("/", response_model=DocumentFolderResponseDTO, status_code=status.HTTP_201_CREATED)
def create_document_folder(
    dto: DocumentFolderCreateDTO,
    created_by: UUID = Query(..., description="User ID creating the folder"),
    use_case: DocumentFolderUseCase = Depends(get_document_folder_use_case),
):
    """Create a new document folder."""
    try:
        return use_case.create_folder(dto, created_by)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{folder_id}", response_model=DocumentFolderDetailResponseDTO)
def get_document_folder(
    folder_id: UUID,
    use_case: DocumentFolderUseCase = Depends(get_document_folder_use_case),
):
    """Get document folder by ID with full details."""
    try:
        folder = use_case.get_folder_by_id(folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document folder not found",
            )
        return folder
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/path/{organization_id}", response_model=DocumentFolderDetailResponseDTO)
def get_folder_by_path(
    organization_id: UUID,
    folder_path: str = Query(..., description="Folder path"),
    use_case: DocumentFolderUseCase = Depends(get_document_folder_use_case),
):
    """Get document folder by path."""
    try:
        folder = use_case.get_folder_by_path(folder_path, organization_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document folder not found",
            )
        return folder
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=DocumentFolderListResponseDTO)
def list_document_folders(
    organization_id: UUID = Query(..., description="Organization ID"),
    area_id: Optional[UUID] = Query(None, description="Filter by area ID"),
    parent_path: Optional[str] = Query(None, description="Filter by parent path"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_inactive: bool = Query(False, description="Include inactive folders"),
    use_case: DocumentFolderUseCase = Depends(get_document_folder_use_case),
):
    """List document folders with pagination."""
    try:
        return use_case.list_folders(
            organization_id=organization_id,
            area_id=area_id,
            parent_path=parent_path,
            page=page,
            page_size=page_size,
            include_inactive=include_inactive,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{folder_id}", response_model=DocumentFolderResponseDTO)
def update_document_folder(
    folder_id: UUID,
    dto: DocumentFolderUpdateDTO,
    updated_by: UUID = Query(..., description="User ID updating the folder"),
    use_case: DocumentFolderUseCase = Depends(get_document_folder_use_case),
):
    """Update document folder information."""
    try:
        updated_folder = use_case.update_folder(folder_id, dto, updated_by)
        if not updated_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document folder not found",
            )
        return updated_folder
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{folder_id}")
def delete_document_folder(
    folder_id: UUID,
    deleted_by: UUID = Query(..., description="User ID deleting the folder"),
    use_case: DocumentFolderUseCase = Depends(get_document_folder_use_case),
):
    """Delete document folder (soft delete)."""
    try:
        success = use_case.delete_folder(folder_id, deleted_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document folder not found",
            )
        return {"message": "Document folder deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{folder_id}/move", response_model=DocumentFolderResponseDTO)
def move_document_folder(
    folder_id: UUID,
    dto: DocumentFolderMoveDTO,
    moved_by: UUID = Query(..., description="User ID moving the folder"),
    use_case: DocumentFolderUseCase = Depends(get_document_folder_use_case),
):
    """Move document folder to a new path."""
    try:
        moved_folder = use_case.move_folder(folder_id, dto, moved_by)
        if not moved_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document folder not found",
            )
        return moved_folder
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/search", response_model=DocumentFolderListResponseDTO)
def search_document_folders(
    dto: DocumentFolderSearchDTO,
    use_case: DocumentFolderUseCase = Depends(get_document_folder_use_case),
):
    """Search document folders."""
    try:
        return use_case.search_folders(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organization/{organization_id}/tree", response_model=List[DocumentFolderTreeResponseDTO])
def get_folder_tree(
    organization_id: UUID,
    area_id: Optional[UUID] = Query(None, description="Filter by area ID"),
    root_path: str = Query("/", description="Root path for tree"),
    use_case: DocumentFolderUseCase = Depends(get_document_folder_use_case),
):
    """Get document folder hierarchy as tree structure."""
    try:
        return use_case.get_folder_tree(
            organization_id=organization_id,
            area_id=area_id,
            root_path=root_path,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/access/check", response_model=DocumentFolderAccessCheckResponseDTO)
def check_folder_access(
    dto: DocumentFolderAccessCheckDTO,
    use_case: DocumentFolderUseCase = Depends(get_document_folder_use_case),
):
    """Check if a user has access to a specific folder."""
    try:
        return use_case.check_folder_access(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk-action", response_model=DocumentFolderBulkActionResponseDTO)
def bulk_action_folders(
    dto: DocumentFolderBulkActionDTO,
    use_case: DocumentFolderUseCase = Depends(get_document_folder_use_case),
):
    """Perform bulk action on document folders."""
    try:
        return use_case.bulk_action(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organization/{organization_id}/stats", response_model=DocumentFolderStatsDTO)
def get_folder_stats(
    organization_id: UUID,
    use_case: DocumentFolderUseCase = Depends(get_document_folder_use_case),
):
    """Get document folder statistics for an organization."""
    try:
        return use_case.get_folder_stats(organization_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))