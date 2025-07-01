from abc import ABC, abstractmethod
from typing import List
from uuid import UUID


class RolePermissionRepository(ABC):
    """Role-Permission repository interface for the Authorization bounded context."""

    @abstractmethod
    def assign_permission_to_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """Assign a permission to a role."""
        pass

    @abstractmethod
    def remove_permission_from_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """Remove a permission from a role."""
        pass

    @abstractmethod
    def get_role_permission_ids(self, role_id: UUID) -> List[UUID]:
        """Get all permission IDs assigned to a role."""
        pass

    @abstractmethod
    def get_permission_role_ids(self, permission_id: UUID) -> List[UUID]:
        """Get all role IDs that have a permission."""
        pass

    @abstractmethod
    def role_has_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        """Check if a role has a specific permission."""
        pass

    @abstractmethod
    def remove_all_role_permissions(self, role_id: UUID) -> int:
        """Remove all permissions from a role. Returns count of removed permissions."""
        pass

    @abstractmethod
    def remove_all_permission_assignments(self, permission_id: UUID) -> int:
        """Remove a permission from all roles. Returns count of removed assignments."""
        pass

    @abstractmethod
    def bulk_assign_permissions_to_role(
        self, role_id: UUID, permission_ids: List[UUID]
    ) -> int:
        """Bulk assign permissions to a role. Returns count of new assignments."""
        pass

    @abstractmethod
    def replace_role_permissions(
        self, role_id: UUID, permission_ids: List[UUID]
    ) -> bool:
        """Replace all permissions for a role with new set."""
        pass
