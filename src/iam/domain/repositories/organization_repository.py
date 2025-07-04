from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.organization import Organization
from ..value_objects.organization_name import OrganizationName


class OrganizationRepository(ABC):
    """Organization repository interface for the Organization bounded context."""

    @abstractmethod
    def save(self, organization: Organization) -> Organization:
        """Save or update an organization."""
        pass

    @abstractmethod
    def get_by_id(self, organization_id: UUID) -> Optional[Organization]:
        """Get organization by ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: OrganizationName) -> Optional[Organization]:
        """Get organization by name."""
        pass

    @abstractmethod
    def get_by_owner_id(self, owner_id: UUID) -> List[Organization]:
        """Get organizations owned by a user."""
        pass

    @abstractmethod
    def exists_by_name(self, name: OrganizationName) -> bool:
        """Check if organization exists by name."""
        pass

    @abstractmethod
    def delete(self, organization_id: UUID) -> bool:
        """Delete organization by ID."""
        pass

    @abstractmethod
    def list_active_organizations(
        self, limit: int = 100, offset: int = 0
    ) -> List[Organization]:
        """List active organizations with pagination."""
        pass

    @abstractmethod
    def count_active_organizations(self) -> int:
        """Count total active organizations."""
        pass

    @abstractmethod
    def get_user_organizations(self, user_id: UUID) -> List[Organization]:
        """Get organizations where user is a member."""
        pass
