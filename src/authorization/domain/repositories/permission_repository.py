from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.permission import Permission, PermissionType
from ..value_objects.permission_name import PermissionName


class PermissionRepository(ABC):
    """Permission repository interface for the Authorization bounded context."""

    @abstractmethod
    def save(self, permission: Permission) -> Permission:
        """Save or update a permission."""
        pass

    @abstractmethod
    def get_by_id(self, permission_id: UUID) -> Optional[Permission]:
        """Get permission by ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: PermissionName) -> Optional[Permission]:
        """Get permission by name."""
        pass

    @abstractmethod
    def get_by_resource_type(self, resource_type: str) -> List[Permission]:
        """Get all permissions for a resource type."""
        pass

    @abstractmethod
    def get_by_resource_and_type(
        self, resource_type: str, permission_type: PermissionType
    ) -> List[Permission]:
        """Get permissions by resource type and permission type."""
        pass

    @abstractmethod
    def get_role_permissions(self, role_id: UUID) -> List[Permission]:
        """Get all permissions assigned to a role."""
        pass

    @abstractmethod
    def get_user_permissions(
        self, user_id: UUID, organization_id: Optional[UUID] = None
    ) -> List[Permission]:
        """Get all permissions for a user (through roles)."""
        pass

    @abstractmethod
    def exists_by_name(self, name: PermissionName) -> bool:
        """Check if permission exists by name."""
        pass

    @abstractmethod
    def delete(self, permission_id: UUID) -> bool:
        """Delete permission by ID."""
        pass

    @abstractmethod
    def list_active_permissions(
        self, limit: int = 100, offset: int = 0
    ) -> List[Permission]:
        """List active permissions with pagination."""
        pass

    @abstractmethod
    def search_permissions(self, query: str, limit: int = 100) -> List[Permission]:
        """Search permissions by name or description."""
        pass
