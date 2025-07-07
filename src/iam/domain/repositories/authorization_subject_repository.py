from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.authorization_subject import AuthorizationSubject


class AuthorizationSubjectRepository(ABC):
    """Abstract repository for AuthorizationSubject entity."""

    @abstractmethod
    def save(self, authorization_subject: AuthorizationSubject) -> AuthorizationSubject:
        """Save an authorization subject."""
        pass

    @abstractmethod
    def find_by_id(self, authorization_subject_id: UUID) -> Optional[AuthorizationSubject]:
        """Find authorization subject by ID."""
        pass

    @abstractmethod
    def find_by_subject(
        self, subject_type: str, subject_id: UUID, organization_id: Optional[UUID] = None
    ) -> Optional[AuthorizationSubject]:
        """Find authorization subject by subject type, ID and organization."""
        pass

    @abstractmethod
    def find_by_owner_id(
        self, owner_id: UUID, organization_id: Optional[UUID] = None
    ) -> List[AuthorizationSubject]:
        """Find all authorization subjects owned by a user."""
        pass

    @abstractmethod
    def find_by_organization_id(self, organization_id: UUID) -> List[AuthorizationSubject]:
        """Find all authorization subjects in an organization."""
        pass

    @abstractmethod
    def find_by_subject_type(
        self, subject_type: str, organization_id: Optional[UUID] = None
    ) -> List[AuthorizationSubject]:
        """Find all authorization subjects of a specific type."""
        pass

    @abstractmethod
    def find_active_by_organization(self, organization_id: UUID) -> List[AuthorizationSubject]:
        """Find all active authorization subjects in an organization."""
        pass

    @abstractmethod
    def find_global_subjects(self) -> List[AuthorizationSubject]:
        """Find all global authorization subjects (not tied to any organization)."""
        pass

    @abstractmethod
    def exists_subject(
        self, subject_type: str, subject_id: UUID, organization_id: Optional[UUID] = None
    ) -> bool:
        """Check if an authorization subject exists."""
        pass

    @abstractmethod
    def delete(self, authorization_subject: AuthorizationSubject) -> bool:
        """Delete an authorization subject."""
        pass

    @abstractmethod
    def delete_by_id(self, authorization_subject_id: UUID) -> bool:
        """Delete authorization subject by ID."""
        pass

    @abstractmethod
    def count_by_owner(self, owner_id: UUID) -> int:
        """Count authorization subjects owned by a user."""
        pass

    @abstractmethod
    def count_by_organization(self, organization_id: UUID) -> int:
        """Count authorization subjects in an organization."""
        pass

    @abstractmethod
    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[UUID] = None,
        subject_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[AuthorizationSubject]:
        """Find authorization subjects with pagination and filters."""
        pass

    @abstractmethod
    def bulk_update_organization(
        self, subject_ids: List[UUID], new_organization_id: Optional[UUID]
    ) -> int:
        """Bulk update organization for multiple subjects."""
        pass

    @abstractmethod
    def bulk_update_owner(self, subject_ids: List[UUID], new_owner_id: UUID) -> int:
        """Bulk update owner for multiple subjects."""
        pass

    @abstractmethod
    def bulk_activate(self, subject_ids: List[UUID]) -> int:
        """Bulk activate multiple authorization subjects."""
        pass

    @abstractmethod
    def bulk_deactivate(self, subject_ids: List[UUID]) -> int:
        """Bulk deactivate multiple authorization subjects."""
        pass