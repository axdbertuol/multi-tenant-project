"""Document Area controller."""

from typing import Optional, List
from uuid import UUID

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


class DocumentAreaController:
    """Controller for document area operations."""

    def __init__(self, use_case: DocumentAreaUseCase):
        self.use_case = use_case

    def create_area(self, dto: DocumentAreaCreateDTO, created_by: UUID) -> DocumentAreaResponseDTO:
        """Create a new document area."""
        return self.use_case.create_area(dto, created_by)

    def get_area_by_id(self, area_id: UUID) -> Optional[DocumentAreaDetailResponseDTO]:
        """Get document area by ID with full details."""
        return self.use_case.get_area_by_id(area_id)

    def list_areas(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        include_system: bool = True,
    ) -> DocumentAreaListResponseDTO:
        """List document areas with pagination."""
        return self.use_case.list_areas(
            organization_id=organization_id,
            page=page,
            page_size=page_size,
            include_system=include_system,
        )

    def update_area(
        self, area_id: UUID, dto: DocumentAreaUpdateDTO, updated_by: UUID
    ) -> Optional[DocumentAreaResponseDTO]:
        """Update document area information."""
        return self.use_case.update_area(area_id, dto, updated_by)

    def delete_area(self, area_id: UUID, deleted_by: UUID) -> bool:
        """Delete document area (soft delete)."""
        return self.use_case.delete_area(area_id, deleted_by)

    def move_area(
        self, area_id: UUID, dto: DocumentAreaMoveDTO, moved_by: UUID
    ) -> Optional[DocumentAreaResponseDTO]:
        """Move document area to a new parent."""
        return self.use_case.move_area(area_id, dto, moved_by)

    def assign_area_to_user(self, dto: DocumentAreaAssignmentDTO) -> bool:
        """Assign document area to a user."""
        return self.use_case.assign_area_to_user(dto)

    def get_area_hierarchy(self, organization_id: UUID) -> DocumentAreaHierarchyResponseDTO:
        """Get document area hierarchy for an organization."""
        return self.use_case.get_area_hierarchy(organization_id)

    def get_area_tree(self, organization_id: UUID) -> List[DocumentAreaTreeResponseDTO]:
        """Get document area hierarchy as tree structure."""
        return self.use_case.get_area_tree(organization_id)

    def check_area_access(self, dto: DocumentAreaAccessDTO) -> DocumentAreaAccessResponseDTO:
        """Check if a user has access to a specific folder through areas."""
        return self.use_case.check_area_access(dto)

    def get_area_stats(self, organization_id: UUID) -> DocumentAreaStatsDTO:
        """Get document area statistics for an organization."""
        return self.use_case.get_area_stats(organization_id)

    def create_default_areas(self, organization_id: UUID) -> List[DocumentAreaResponseDTO]:
        """Create default document areas for an organization."""
        return self.use_case.create_default_areas(organization_id)