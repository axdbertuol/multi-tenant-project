from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ..entities.role import Role
from ..value_objects.role_name import RoleName


class RoleRepository(ABC):
    """Role repository interface for the Authorization bounded context."""

    @abstractmethod
    def save(self, role: Role) -> Role:
        """Save or update a role."""
        pass

    @abstractmethod
    def get_by_id(self, role_id: UUID) -> Optional[Role]:
        """Get role by ID."""
        pass

    @abstractmethod
    def get_by_name(
        self, name: RoleName, organization_id: Optional[UUID] = None
    ) -> Optional[Role]:
        """Get role by name within organization scope."""
        pass

    @abstractmethod
    def get_organization_roles(self, organization_id: UUID) -> List[Role]:
        """Get all roles for an organization."""
        pass

    @abstractmethod
    def get_system_roles(self) -> List[Role]:
        """Get all system roles."""
        pass

    @abstractmethod
    def get_user_roles(
        self, user_id: UUID, organization_id: Optional[UUID] = None
    ) -> List[Role]:
        """Get roles assigned to a user."""
        pass

    @abstractmethod
    def exists_by_name(
        self, name: RoleName, organization_id: Optional[UUID] = None
    ) -> bool:
        """Check if role exists by name within organization scope."""
        pass

    @abstractmethod
    def delete(self, role_id: UUID) -> bool:
        """Delete role by ID."""
        pass

    @abstractmethod
    def list_active_roles(
        self, organization_id: Optional[UUID] = None, limit: int = 100, offset: int = 0
    ) -> List[Role]:
        """List active roles with pagination."""
        pass

    @abstractmethod
    def count_role_assignments(self, role_id: UUID) -> int:
        """Count how many users have this role assigned."""
        pass

    @abstractmethod
    def get_child_roles(self, parent_role_id: UUID) -> List[Role]:
        """Get all direct child roles of a parent role."""
        pass

    @abstractmethod
    def get_roles_by_parent(self, parent_role_id: Optional[UUID]) -> List[Role]:
        """Get all roles with the specified parent (None for root roles)."""
        pass

    @abstractmethod
    def get_role_hierarchy(self, organization_id: Optional[UUID] = None) -> List[Role]:
        """Get all roles in hierarchical order for an organization."""
        pass

    @abstractmethod
    def has_child_roles(self, role_id: UUID) -> bool:
        """Check if role has any child roles."""
        pass

    @abstractmethod
    def get_root_roles(self, organization_id: Optional[UUID] = None) -> List[Role]:
        """Get all root roles (roles with no parent) for an organization."""
        pass

    @abstractmethod
    def find_paginated(
        self,
        organization_id: Optional[UUID],
        include_system: bool,
        offset: int,
        limit: int,
    ) -> tuple[List[Role], int]:
        pass

    @abstractmethod
    def get_assignment_count(self, role_id: UUID) -> int:
        pass

    @abstractmethod
    def assign_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        pass

    @abstractmethod
    def replace_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        pass

    @abstractmethod
    def remove_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        pass

    @abstractmethod
    def get_role_permissions(self, role_id: UUID) -> List[Role]:
        pass

    @abstractmethod
    def get_permission_count(self, role_id: UUID) -> int:
        pass

    @abstractmethod
    def assign_role_to_user(
        self,
        user_id: UUID,
        role_id: UUID,
        assigned_by: UUID,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """Assign a role to a user."""
        pass

    @abstractmethod
    def remove_role_from_user(self, user_id: UUID, role_id: UUID) -> bool:
        """Remove a role from a user."""
        pass

    @abstractmethod
    def get_user_roles_in_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> List[Role]:
        """Get roles assigned to a user that belong to a specific organization."""
        pass

    @abstractmethod
    def get_users_with_role_in_organization(
        self, role_id: UUID, organization_id: UUID
    ) -> List[UUID]:
        """Get all users that have a specific role and belong to a specific organization."""
        pass

    @abstractmethod
    def remove_all_user_roles(self, user_id: UUID) -> bool:
        """Remove all roles from a user (typically when user leaves organization)."""
        pass
