from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.permission import Permission, PermissionAction
from ..value_objects.permission_name import PermissionName


class PermissionRepository(ABC):
    """Permission repository interface for the Authorization bounded context."""

    @abstractmethod
    def save(self, permission: Permission) -> Permission:
        """Save or update a permission."""
        pass

    @abstractmethod
    def find_by_id(self, permission_id: UUID) -> Optional[Permission]:
        """Get permission by ID."""
        pass

    @abstractmethod
    def find_by_name_and_resource(
        self, name: str, resource_type: str
    ) -> Optional[Permission]:
        """Get permission by name and resource type."""
        pass

    @abstractmethod
    def find_by_resource_type(self, resource_type: str) -> List[Permission]:
        """Get all permissions for a resource type."""
        pass

    @abstractmethod
    def get_by_resource_and_type(
        self, resource_type: str, permission_type: PermissionAction
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
    def find_paginated(
        self, include_system: bool, offset: int, limit: int
    ) -> tuple[List[Permission], int]:
        pass

    @abstractmethod
    def search(
        self,
        query: Optional[str],
        resource_type: Optional[str],
        action: Optional[PermissionAction],
        is_active: Optional[bool],
        offset: int,
        limit: int,
    ) -> tuple[List[Permission], int]:
        pass

    @abstractmethod
    def get_role_count(self, permission_id: UUID) -> int:
        pass

    @abstractmethod
    def find_system_permissions(self) -> List[Permission]:
        pass

    @abstractmethod
    def bulk_save(self, permissions: List[Permission]) -> List[Permission]:
        pass

    @abstractmethod
    def find_by_ids(self, permission_ids: List[UUID]) -> List[Permission]:
        pass
