from typing import List, Optional, Dict, Any
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork
from ..dtos.authorization_subject_dto import (
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
    entity_to_response_dto,
    entities_to_list_response_dto,
    bulk_result_to_response_dto,
)
from ...domain.entities.authorization_subject import AuthorizationSubject
from ...domain.repositories.authorization_subject_repository import AuthorizationSubjectRepository
from ...domain.services.authorization_subject_service import AuthorizationSubjectService


class AuthorizationSubjectUseCase:
    """Use case for authorization subject management operations."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._repository: AuthorizationSubjectRepository = uow.get_repository("authorization_subject")
        self._service = AuthorizationSubjectService(self._repository)

    def create_subject(
        self, dto: AuthorizationSubjectCreateDTO, requester_id: UUID
    ) -> AuthorizationSubjectResponseDTO:
        """Create a new authorization subject."""
        try:
            with self._uow:
                subject = self._service.register_subject(
                    subject_type=dto.subject_type,
                    subject_id=dto.subject_id,
                    owner_id=dto.owner_id,
                    organization_id=dto.organization_id,
                )
                
                return entity_to_response_dto(subject)
                
        except ValueError as e:
            raise ValueError(f"Failed to create authorization subject: {str(e)}")

    def get_subject_by_id(self, subject_id: UUID) -> Optional[AuthorizationSubjectResponseDTO]:
        """Get authorization subject by ID."""
        subject = self._repository.find_by_id(subject_id)
        return entity_to_response_dto(subject) if subject else None

    def update_subject(
        self, subject_id: UUID, dto: AuthorizationSubjectUpdateDTO, requester_id: UUID
    ) -> AuthorizationSubjectResponseDTO:
        """Update an authorization subject."""
        subject = self._repository.find_by_id(subject_id)
        if not subject:
            raise ValueError(f"Authorization subject not found: {subject_id}")

        # Verify ownership
        if not subject.is_owned_by(requester_id):
            raise ValueError("Only the owner can update the subject")

        try:
            with self._uow:
                updated_subject = subject
                
                if dto.is_active is not None:
                    if dto.is_active and not subject.is_active:
                        updated_subject = subject.activate()
                    elif not dto.is_active and subject.is_active:
                        updated_subject = subject.deactivate()
                
                if updated_subject != subject:
                    updated_subject = self._repository.save(updated_subject)
                
                return entity_to_response_dto(updated_subject)
                
        except Exception as e:
            raise ValueError(f"Failed to update authorization subject: {str(e)}")

    def transfer_ownership(
        self, subject_id: UUID, dto: AuthorizationSubjectTransferOwnershipDTO, requester_id: UUID
    ) -> AuthorizationSubjectResponseDTO:
        """Transfer ownership of an authorization subject."""
        try:
            with self._uow:
                updated_subject = self._service.transfer_ownership(
                    subject_id=subject_id,
                    new_owner_id=dto.new_owner_id,
                    current_owner_id=requester_id,
                )
                
                return entity_to_response_dto(updated_subject)
                
        except ValueError as e:
            raise ValueError(f"Failed to transfer ownership: {str(e)}")

    def move_to_organization(
        self, subject_id: UUID, dto: AuthorizationSubjectMoveOrganizationDTO, requester_id: UUID
    ) -> AuthorizationSubjectResponseDTO:
        """Move authorization subject to different organization."""
        try:
            with self._uow:
                updated_subject = self._service.move_to_organization(
                    subject_id=subject_id,
                    organization_id=dto.organization_id,
                    requester_id=requester_id,
                )
                
                return entity_to_response_dto(updated_subject)
                
        except ValueError as e:
            raise ValueError(f"Failed to move subject to organization: {str(e)}")

    def activate_subject(self, subject_id: UUID, requester_id: UUID) -> AuthorizationSubjectResponseDTO:
        """Activate an authorization subject."""
        try:
            with self._uow:
                updated_subject = self._service.activate_subject(
                    subject_id=subject_id,
                    requester_id=requester_id,
                )
                
                return entity_to_response_dto(updated_subject)
                
        except ValueError as e:
            raise ValueError(f"Failed to activate subject: {str(e)}")

    def deactivate_subject(self, subject_id: UUID, requester_id: UUID) -> AuthorizationSubjectResponseDTO:
        """Deactivate an authorization subject."""
        try:
            with self._uow:
                updated_subject = self._service.deactivate_subject(
                    subject_id=subject_id,
                    requester_id=requester_id,
                )
                
                return entity_to_response_dto(updated_subject)
                
        except ValueError as e:
            raise ValueError(f"Failed to deactivate subject: {str(e)}")

    def delete_subject(self, subject_id: UUID, requester_id: UUID) -> bool:
        """Delete an authorization subject."""
        subject = self._repository.find_by_id(subject_id)
        if not subject:
            raise ValueError(f"Authorization subject not found: {subject_id}")

        # Verify ownership
        if not subject.is_owned_by(requester_id):
            raise ValueError("Only the owner can delete the subject")

        try:
            with self._uow:
                return self._repository.delete(subject)
                
        except Exception as e:
            raise ValueError(f"Failed to delete authorization subject: {str(e)}")

    def find_subject_by_reference(
        self, dto: AuthorizationSubjectSearchDTO
    ) -> Optional[AuthorizationSubjectResponseDTO]:
        """Find authorization subject by external reference."""
        subject = self._service.find_subject_by_reference(
            subject_type=dto.subject_type,
            subject_id=dto.subject_id,
            organization_id=dto.organization_id,
        )
        return entity_to_response_dto(subject) if subject else None

    def list_subjects(self, filters: AuthorizationSubjectFilterDTO) -> AuthorizationSubjectListResponseDTO:
        """List authorization subjects with pagination and filters."""
        subjects = self._repository.find_all(
            skip=(filters.page - 1) * filters.page_size,
            limit=filters.page_size,
            organization_id=filters.organization_id,
            subject_type=filters.subject_type,
            is_active=filters.is_active,
        )
        
        # Get total count for pagination
        # Note: This is a simplified approach. In production, you might want a separate count method
        all_subjects = self._repository.find_all(
            skip=0,
            limit=10000,  # Large number to get all for counting
            organization_id=filters.organization_id,
            subject_type=filters.subject_type,
            is_active=filters.is_active,
        )
        total = len(all_subjects)
        
        return entities_to_list_response_dto(subjects, total, filters.page, filters.page_size)

    def get_user_subjects(
        self, user_id: UUID, organization_id: Optional[UUID] = None
    ) -> List[AuthorizationSubjectResponseDTO]:
        """Get all subjects owned by a user."""
        subjects = self._service.get_user_subjects(user_id, organization_id)
        return [entity_to_response_dto(subject) for subject in subjects]

    def get_organization_subjects(
        self, organization_id: UUID, subject_type: Optional[str] = None
    ) -> List[AuthorizationSubjectResponseDTO]:
        """Get all subjects in an organization."""
        subjects = self._service.get_organization_subjects(organization_id, subject_type)
        return [entity_to_response_dto(subject) for subject in subjects]

    def get_active_organization_subjects(
        self, organization_id: UUID
    ) -> List[AuthorizationSubjectResponseDTO]:
        """Get all active subjects in an organization."""
        subjects = self._service.get_active_organization_subjects(organization_id)
        return [entity_to_response_dto(subject) for subject in subjects]

    def bulk_transfer_ownership(
        self, dto: BulkTransferOwnershipDTO, requester_id: UUID
    ) -> BulkOperationResponseDTO:
        """Bulk transfer ownership of multiple subjects."""
        try:
            with self._uow:
                result = self._service.bulk_transfer_ownership(
                    subject_ids=dto.subject_ids,
                    new_owner_id=dto.new_owner_id,
                    current_owner_id=requester_id,
                )
                
                return bulk_result_to_response_dto(result, len(dto.subject_ids))
                
        except Exception as e:
            return BulkOperationResponseDTO(
                updated_count=0,
                errors=[str(e)],
                total_requested=len(dto.subject_ids),
                success_rate=0.0,
            )

    def bulk_move_to_organization(
        self, dto: BulkMoveOrganizationDTO, requester_id: UUID
    ) -> BulkOperationResponseDTO:
        """Bulk move subjects to different organization."""
        try:
            with self._uow:
                result = self._service.bulk_move_to_organization(
                    subject_ids=dto.subject_ids,
                    organization_id=dto.organization_id,
                    requester_id=requester_id,
                )
                
                return bulk_result_to_response_dto(result, len(dto.subject_ids))
                
        except Exception as e:
            return BulkOperationResponseDTO(
                updated_count=0,
                errors=[str(e)],
                total_requested=len(dto.subject_ids),
                success_rate=0.0,
            )

    def bulk_activate_subjects(
        self, dto: BulkAuthorizationSubjectOperationDTO, requester_id: UUID
    ) -> BulkOperationResponseDTO:
        """Bulk activate multiple subjects."""
        try:
            with self._uow:
                result = self._service.bulk_activate_subjects(
                    subject_ids=dto.subject_ids,
                    requester_id=requester_id,
                )
                
                return bulk_result_to_response_dto(result, len(dto.subject_ids))
                
        except Exception as e:
            return BulkOperationResponseDTO(
                updated_count=0,
                errors=[str(e)],
                total_requested=len(dto.subject_ids),
                success_rate=0.0,
            )

    def bulk_deactivate_subjects(
        self, dto: BulkAuthorizationSubjectOperationDTO, requester_id: UUID
    ) -> BulkOperationResponseDTO:
        """Bulk deactivate multiple subjects."""
        try:
            with self._uow:
                result = self._service.bulk_deactivate_subjects(
                    subject_ids=dto.subject_ids,
                    requester_id=requester_id,
                )
                
                return bulk_result_to_response_dto(result, len(dto.subject_ids))
                
        except Exception as e:
            return BulkOperationResponseDTO(
                updated_count=0,
                errors=[str(e)],
                total_requested=len(dto.subject_ids),
                success_rate=0.0,
            )

    def get_subject_statistics(
        self, organization_id: Optional[UUID] = None
    ) -> AuthorizationSubjectStatisticsDTO:
        """Get statistics about authorization subjects."""
        stats = self._service.get_subject_statistics(organization_id)
        
        return AuthorizationSubjectStatisticsDTO(
            total_subjects=stats["total_subjects"],
            active_subjects=stats["active_subjects"],
            inactive_subjects=stats["inactive_subjects"],
            subjects_by_type=stats["subjects_by_type"],
            organization_id=stats["organization_id"],
        )