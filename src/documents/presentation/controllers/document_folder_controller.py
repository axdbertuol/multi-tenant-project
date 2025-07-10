"""Document Folder controller."""

from typing import Optional, List
from uuid import UUID

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


class DocumentFolderController:
    """Controller for document folder operations."""

    def __init__(self, use_case: DocumentFolderUseCase):
        self.use_case = use_case

    def create_folder(self, dto: DocumentFolderCreateDTO, created_by: UUID) -> DocumentFolderResponseDTO:
        """Create a new document folder."""
        return self.use_case.create_folder(dto, created_by)

    def get_folder_by_id(self, folder_id: UUID) -> Optional[DocumentFolderDetailResponseDTO]:
        """Get document folder by ID with full details."""
        return self.use_case.get_folder_by_id(folder_id)

    def get_folder_by_path(self, folder_path: str, organization_id: UUID) -> Optional[DocumentFolderDetailResponseDTO]:
        """Get document folder by path."""
        return self.use_case.get_folder_by_path(folder_path, organization_id)

    def list_folders(
        self,
        organization_id: UUID,
        area_id: Optional[UUID] = None,
        parent_path: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        include_inactive: bool = False,
    ) -> DocumentFolderListResponseDTO:
        """List document folders with pagination."""
        return self.use_case.list_folders(
            organization_id=organization_id,
            area_id=area_id,
            parent_path=parent_path,
            page=page,
            page_size=page_size,
            include_inactive=include_inactive,
        )

    def update_folder(
        self, folder_id: UUID, dto: DocumentFolderUpdateDTO, updated_by: UUID
    ) -> Optional[DocumentFolderResponseDTO]:
        """Update document folder information."""
        return self.use_case.update_folder(folder_id, dto, updated_by)

    def delete_folder(self, folder_id: UUID, deleted_by: UUID) -> bool:
        """Delete document folder (soft delete)."""
        return self.use_case.delete_folder(folder_id, deleted_by)

    def move_folder(
        self, folder_id: UUID, dto: DocumentFolderMoveDTO, moved_by: UUID
    ) -> Optional[DocumentFolderResponseDTO]:
        """Move document folder to a new path."""
        return self.use_case.move_folder(folder_id, dto, moved_by)

    def search_folders(self, dto: DocumentFolderSearchDTO) -> DocumentFolderListResponseDTO:
        """Search document folders."""
        return self.use_case.search_folders(dto)

    def get_folder_tree(
        self,
        organization_id: UUID,
        area_id: Optional[UUID] = None,
        root_path: str = "/",
    ) -> List[DocumentFolderTreeResponseDTO]:
        """Get document folder hierarchy as tree structure."""
        return self.use_case.get_folder_tree(
            organization_id=organization_id,
            area_id=area_id,
            root_path=root_path,
        )

    def check_folder_access(self, dto: DocumentFolderAccessCheckDTO) -> DocumentFolderAccessCheckResponseDTO:
        """Check if a user has access to a specific folder."""
        return self.use_case.check_folder_access(dto)

    def bulk_action(self, dto: DocumentFolderBulkActionDTO) -> DocumentFolderBulkActionResponseDTO:
        """Perform bulk action on document folders."""
        return self.use_case.bulk_action(dto)

    def get_folder_stats(self, organization_id: UUID) -> DocumentFolderStatsDTO:
        """Get document folder statistics for an organization."""
        return self.use_case.get_folder_stats(organization_id)