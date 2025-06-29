from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.resource import Resource, ResourceType
from .base_repository import Repository


class ResourceRepository(Repository[Resource]):
    @abstractmethod
    async def find_by_name(self, name: str, organization_id: Optional[UUID] = None) -> Optional[Resource]:
        pass

    @abstractmethod
    async def find_by_type(self, resource_type: ResourceType, organization_id: Optional[UUID] = None) -> List[Resource]:
        pass

    @abstractmethod
    async def find_by_parent_id(self, parent_id: UUID) -> List[Resource]:
        pass

    @abstractmethod
    async def find_by_organization(self, organization_id: UUID) -> List[Resource]:
        pass

    @abstractmethod
    async def find_by_metadata_attribute(self, key: str, value: str, organization_id: Optional[UUID] = None) -> List[Resource]:
        pass

    @abstractmethod
    async def find_hierarchical_children(self, parent_id: UUID, recursive: bool = False) -> List[Resource]:
        pass

    @abstractmethod
    async def find_active_resources(self, organization_id: Optional[UUID] = None) -> List[Resource]:
        pass