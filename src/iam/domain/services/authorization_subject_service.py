from typing import List, Optional, Dict, Any
from uuid import UUID

from ..entities.authorization_subject import AuthorizationSubject
from ..repositories.authorization_subject_repository import AuthorizationSubjectRepository


class AuthorizationSubjectService:
    """Domain service for AuthorizationSubject business logic."""

    def __init__(self, authorization_subject_repository: AuthorizationSubjectRepository):
        self._repository = authorization_subject_repository

    def register_subject(
        self,
        subject_type: str,
        subject_id: UUID,
        owner_id: UUID,
        organization_id: Optional[UUID] = None,
    ) -> AuthorizationSubject:
        """Register a new authorization subject."""
        # Check if subject already exists
        if self._repository.exists_subject(subject_type, subject_id, organization_id):
            raise ValueError(
                f"Authorization subject already exists: {subject_type}:{subject_id} "
                f"in organization {organization_id}"
            )

        # Create new subject
        subject = AuthorizationSubject.create(
            subject_type=subject_type,
            subject_id=subject_id,
            owner_id=owner_id,
            organization_id=organization_id,
        )

        return self._repository.save(subject)

    def transfer_ownership(
        self, subject_id: UUID, new_owner_id: UUID, current_owner_id: UUID
    ) -> AuthorizationSubject:
        """Transfer ownership of an authorization subject."""
        subject = self._repository.find_by_id(subject_id)
        if not subject:
            raise ValueError(f"Authorization subject not found: {subject_id}")

        # Verify current ownership
        if not subject.is_owned_by(current_owner_id):
            raise ValueError("Only the current owner can transfer ownership")

        # Transfer ownership
        updated_subject = subject.update_owner(new_owner_id)
        return self._repository.save(updated_subject)

    def move_to_organization(
        self, subject_id: UUID, organization_id: Optional[UUID], requester_id: UUID
    ) -> AuthorizationSubject:
        """Move an authorization subject to a different organization."""
        subject = self._repository.find_by_id(subject_id)
        if not subject:
            raise ValueError(f"Authorization subject not found: {subject_id}")

        # Verify ownership or organization admin rights
        if not subject.is_owned_by(requester_id):
            # TODO: Add organization admin check when available
            raise ValueError("Only the owner can move the subject between organizations")

        # Check if subject would conflict in target organization
        if self._repository.exists_subject(
            subject.subject_type, subject.subject_id, organization_id
        ):
            raise ValueError(
                f"Subject already exists in target organization: "
                f"{subject.subject_type}:{subject.subject_id}"
            )

        # Update organization
        updated_subject = subject.update_organization(organization_id)
        return self._repository.save(updated_subject)

    def activate_subject(self, subject_id: UUID, requester_id: UUID) -> AuthorizationSubject:
        """Activate an authorization subject."""
        subject = self._repository.find_by_id(subject_id)
        if not subject:
            raise ValueError(f"Authorization subject not found: {subject_id}")

        # Verify ownership
        if not subject.is_owned_by(requester_id):
            raise ValueError("Only the owner can activate the subject")

        # Activate
        updated_subject = subject.activate()
        return self._repository.save(updated_subject)

    def deactivate_subject(self, subject_id: UUID, requester_id: UUID) -> AuthorizationSubject:
        """Deactivate an authorization subject."""
        subject = self._repository.find_by_id(subject_id)
        if not subject:
            raise ValueError(f"Authorization subject not found: {subject_id}")

        # Verify ownership
        if not subject.is_owned_by(requester_id):
            raise ValueError("Only the owner can deactivate the subject")

        # Deactivate
        updated_subject = subject.deactivate()
        return self._repository.save(updated_subject)

    def get_user_subjects(
        self, user_id: UUID, organization_id: Optional[UUID] = None
    ) -> List[AuthorizationSubject]:
        """Get all subjects owned by a user."""
        return self._repository.find_by_owner_id(user_id, organization_id)

    def get_organization_subjects(
        self, organization_id: UUID, subject_type: Optional[str] = None
    ) -> List[AuthorizationSubject]:
        """Get all subjects in an organization."""
        if subject_type:
            return self._repository.find_by_subject_type(subject_type, organization_id)
        else:
            return self._repository.find_by_organization_id(organization_id)

    def get_active_organization_subjects(self, organization_id: UUID) -> List[AuthorizationSubject]:
        """Get all active subjects in an organization."""
        return self._repository.find_active_by_organization(organization_id)

    def find_subject_by_reference(
        self, subject_type: str, subject_id: UUID, organization_id: Optional[UUID] = None
    ) -> Optional[AuthorizationSubject]:
        """Find subject by its external reference."""
        return self._repository.find_by_subject(subject_type, subject_id, organization_id)

    def bulk_transfer_ownership(
        self, subject_ids: List[UUID], new_owner_id: UUID, current_owner_id: UUID
    ) -> Dict[str, Any]:
        """Bulk transfer ownership of multiple subjects."""
        if not subject_ids:
            return {"updated_count": 0, "errors": []}

        # Verify ownership of all subjects
        subjects = []
        errors = []
        
        for subject_id in subject_ids:
            subject = self._repository.find_by_id(subject_id)
            if not subject:
                errors.append(f"Subject not found: {subject_id}")
                continue
            
            if not subject.is_owned_by(current_owner_id):
                errors.append(f"Not authorized to transfer subject: {subject_id}")
                continue
            
            subjects.append(subject)

        # If there are errors, don't proceed with any transfers
        if errors:
            return {"updated_count": 0, "errors": errors}

        # Perform bulk update
        valid_ids = [subject.id for subject in subjects]
        updated_count = self._repository.bulk_update_owner(valid_ids, new_owner_id)

        return {"updated_count": updated_count, "errors": []}

    def bulk_move_to_organization(
        self, subject_ids: List[UUID], organization_id: Optional[UUID], requester_id: UUID
    ) -> Dict[str, Any]:
        """Bulk move subjects to a different organization."""
        if not subject_ids:
            return {"updated_count": 0, "errors": []}

        # Verify ownership and no conflicts
        subjects = []
        errors = []
        
        for subject_id in subject_ids:
            subject = self._repository.find_by_id(subject_id)
            if not subject:
                errors.append(f"Subject not found: {subject_id}")
                continue
            
            if not subject.is_owned_by(requester_id):
                errors.append(f"Not authorized to move subject: {subject_id}")
                continue
            
            # Check for conflicts in target organization
            if self._repository.exists_subject(
                subject.subject_type, subject.subject_id, organization_id
            ):
                errors.append(
                    f"Subject would conflict in target organization: {subject_id}"
                )
                continue
            
            subjects.append(subject)

        # If there are errors, don't proceed with any moves
        if errors:
            return {"updated_count": 0, "errors": errors}

        # Perform bulk update
        valid_ids = [subject.id for subject in subjects]
        updated_count = self._repository.bulk_update_organization(valid_ids, organization_id)

        return {"updated_count": updated_count, "errors": []}

    def bulk_activate_subjects(
        self, subject_ids: List[UUID], requester_id: UUID
    ) -> Dict[str, Any]:
        """Bulk activate multiple subjects."""
        if not subject_ids:
            return {"updated_count": 0, "errors": []}

        # Verify ownership of all subjects
        subjects = []
        errors = []
        
        for subject_id in subject_ids:
            subject = self._repository.find_by_id(subject_id)
            if not subject:
                errors.append(f"Subject not found: {subject_id}")
                continue
            
            if not subject.is_owned_by(requester_id):
                errors.append(f"Not authorized to activate subject: {subject_id}")
                continue
            
            subjects.append(subject)

        # If there are errors, don't proceed with any activations
        if errors:
            return {"updated_count": 0, "errors": errors}

        # Perform bulk activation
        valid_ids = [subject.id for subject in subjects]
        updated_count = self._repository.bulk_activate(valid_ids)

        return {"updated_count": updated_count, "errors": []}

    def bulk_deactivate_subjects(
        self, subject_ids: List[UUID], requester_id: UUID
    ) -> Dict[str, Any]:
        """Bulk deactivate multiple subjects."""
        if not subject_ids:
            return {"updated_count": 0, "errors": []}

        # Verify ownership of all subjects
        subjects = []
        errors = []
        
        for subject_id in subject_ids:
            subject = self._repository.find_by_id(subject_id)
            if not subject:
                errors.append(f"Subject not found: {subject_id}")
                continue
            
            if not subject.is_owned_by(requester_id):
                errors.append(f"Not authorized to deactivate subject: {subject_id}")
                continue
            
            subjects.append(subject)

        # If there are errors, don't proceed with any deactivations
        if errors:
            return {"updated_count": 0, "errors": errors}

        # Perform bulk deactivation
        valid_ids = [subject.id for subject in subjects]
        updated_count = self._repository.bulk_deactivate(valid_ids)

        return {"updated_count": updated_count, "errors": []}

    def get_subject_statistics(self, organization_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get statistics about authorization subjects."""
        if organization_id:
            total_count = self._repository.count_by_organization(organization_id)
            subjects = self._repository.find_by_organization_id(organization_id)
        else:
            # Global statistics - would need a count_all method
            subjects = self._repository.find_global_subjects()
            total_count = len(subjects)

        active_count = sum(1 for s in subjects if s.is_active)
        inactive_count = total_count - active_count

        # Group by subject type
        type_counts = {}
        for subject in subjects:
            type_counts[subject.subject_type] = type_counts.get(subject.subject_type, 0) + 1

        return {
            "total_subjects": total_count,
            "active_subjects": active_count,
            "inactive_subjects": inactive_count,
            "subjects_by_type": type_counts,
            "organization_id": str(organization_id) if organization_id else None,
        }