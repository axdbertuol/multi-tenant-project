"""User Document Access controller."""

from typing import Optional, List
from uuid import UUID

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


class UserDocumentAccessController:
    """Controller for user document access operations."""

    def __init__(self, use_case: UserDocumentAccessUseCase):
        self.use_case = use_case

    def create_access(self, dto: UserDocumentAccessCreateDTO) -> UserDocumentAccessResponseDTO:
        """Create a new user document access."""
        return self.use_case.create_access(dto)

    def get_access_by_id(self, access_id: UUID) -> Optional[UserDocumentAccessDetailResponseDTO]:
        """Get user document access by ID with full details."""
        return self.use_case.get_access_by_id(access_id)

    def list_accesses(
        self,
        filters: Optional[UserDocumentAccessFilterDTO] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> UserDocumentAccessListResponseDTO:
        """List user document accesses with filtering and pagination."""
        return self.use_case.list_accesses(filters, page, page_size)

    def update_access(
        self, access_id: UUID, dto: UserDocumentAccessUpdateDTO
    ) -> Optional[UserDocumentAccessResponseDTO]:
        """Update user document access information."""
        return self.use_case.update_access(access_id, dto)

    def delete_access(self, access_id: UUID) -> bool:
        """Delete user document access."""
        return self.use_case.delete_access(access_id)

    def revoke_access(self, dto: UserDocumentAccessRevokeDTO) -> bool:
        """Revoke user document access."""
        return self.use_case.revoke_access(dto)

    def extend_access(
        self, access_id: UUID, dto: UserDocumentAccessExtendDTO
    ) -> Optional[UserDocumentAccessResponseDTO]:
        """Extend user document access expiration."""
        return self.use_case.extend_access(access_id, dto)

    def batch_create_accesses(
        self, dto: UserDocumentAccessBatchCreateDTO
    ) -> List[UserDocumentAccessResponseDTO]:
        """Create multiple user document accesses."""
        return self.use_case.batch_create_accesses(dto)

    def transfer_accesses(
        self, dto: UserDocumentAccessTransferDTO
    ) -> List[UserDocumentAccessResponseDTO]:
        """Transfer user accesses from one area to another."""
        return self.use_case.transfer_accesses(dto)

    def bulk_action(
        self, dto: UserDocumentAccessBulkActionDTO
    ) -> UserDocumentAccessBulkActionResponseDTO:
        """Perform bulk action on user document accesses."""
        return self.use_case.bulk_action(dto)

    def get_access_stats(
        self, organization_id: Optional[UUID] = None
    ) -> UserDocumentAccessStatsDTO:
        """Get user document access statistics."""
        return self.use_case.get_access_stats(organization_id)