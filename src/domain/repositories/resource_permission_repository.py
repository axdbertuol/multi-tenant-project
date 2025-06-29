from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.resource_permission import ResourcePermission, PermissionEffect
from .base_repository import Repository


class ResourcePermissionRepository(Repository[ResourcePermission]):
    @abstractmethod
    async def find_by_user_and_resource(self, user_id: UUID, resource_id: UUID) -> List[ResourcePermission]:
        pass

    @abstractmethod
    async def find_by_role_and_resource(self, role_id: UUID, resource_id: UUID) -> List[ResourcePermission]:
        pass

    @abstractmethod
    async def find_by_user(self, user_id: UUID) -> List[ResourcePermission]:
        pass

    @abstractmethod
    async def find_by_resource(self, resource_id: UUID) -> List[ResourcePermission]:
        pass

    @abstractmethod
    async def find_by_permission_and_resource(self, permission_id: UUID, resource_id: UUID) -> List[ResourcePermission]:
        pass

    @abstractmethod
    async def find_effective_permissions(
        self,
        user_id: UUID,
        resource_id: UUID,
        permission_id: UUID,
        user_roles: List[UUID],
    ) -> List[ResourcePermission]:
        """Find all permissions (user + role-based) for a specific user, resource, and permission"""
        pass

    @abstractmethod
    async def find_active_by_user_and_resource(self, user_id: UUID, resource_id: UUID) -> List[ResourcePermission]:
        pass

    @abstractmethod
    async def find_by_effect(self, effect: PermissionEffect) -> List[ResourcePermission]:
        pass