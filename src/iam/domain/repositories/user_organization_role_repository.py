from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.user_organization_role import UserOrganizationRole


class UserOrganizationRoleRepository(ABC):
    """User organization role repository interface for the Organization bounded context."""

    @abstractmethod
    def save(self, role: UserOrganizationRole) -> UserOrganizationRole:
        """Save or update a user organization role."""
        pass

    @abstractmethod
    def get_by_id(self, role_id: UUID) -> Optional[UserOrganizationRole]:
        """Get role by ID."""
        pass

    @abstractmethod
    def get_by_user_and_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> Optional[UserOrganizationRole]:
        """Get role by user and organization."""
        pass

    @abstractmethod
    def get_user_roles_in_organization(
        self, organization_id: UUID
    ) -> List[UserOrganizationRole]:
        """Get all user roles in an organization."""
        pass

    @abstractmethod
    def get_user_organizations(self, user_id: UUID) -> List[UserOrganizationRole]:
        """Get all organizations where user has a role."""
        pass

    @abstractmethod
    def user_has_role_in_organization(
        self, user_id: UUID, organization_id: UUID, role_id: UUID
    ) -> bool:
        """Check if user has specific role in organization."""
        pass

    @abstractmethod
    def count_organization_users(self, organization_id: UUID) -> int:
        """Count active users in organization."""
        pass

    @abstractmethod
    def remove_user_from_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> bool:
        """Remove user from organization."""
        pass

    @abstractmethod
    def delete(self, role_id: UUID) -> bool:
        """Delete role by ID."""
        pass

    @abstractmethod
    def cleanup_expired_roles(self) -> int:
        """Cleanup expired roles. Returns count of cleaned roles."""
        pass

    @abstractmethod
    def assign_role_to_user(
        self, user_id: UUID, organization_id: UUID, role_id: UUID
    ) -> None:
        """Assign a role to a user in an organization."""
        pass
