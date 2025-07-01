from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..entities.resource import Resource


class ResourceRepository(ABC):
    """Resource repository interface for the Authorization bounded context."""

    @abstractmethod
    def save(self, resource: Resource) -> Resource:
        """Save or update a resource."""
        pass

    @abstractmethod
    def get_by_id(self, resource_id: UUID) -> Optional[Resource]:
        """Get resource by ID."""
        pass

    @abstractmethod
    def get_by_resource_id(
        self, resource_type: str, resource_id: UUID
    ) -> Optional[Resource]:
        """Get resource by type and actual resource ID."""
        pass

    @abstractmethod
    def get_by_owner_id(self, owner_id: UUID) -> List[Resource]:
        """Get all resources owned by a user."""
        pass

    @abstractmethod
    def get_by_organization_id(self, organization_id: UUID) -> List[Resource]:
        """Get all resources belonging to an organization."""
        pass

    @abstractmethod
    def get_by_type(self, resource_type: str) -> List[Resource]:
        """Get all resources of a specific type."""
        pass

    @abstractmethod
    def find_by_attributes(
        self, resource_type: str, attributes: Dict[str, Any]
    ) -> List[Resource]:
        """Find resources by attributes."""
        pass

    @abstractmethod
    def delete(self, resource_id: UUID) -> bool:
        """Delete resource by ID."""
        pass

    @abstractmethod
    def delete_by_resource_id(self, resource_type: str, resource_id: UUID) -> bool:
        """Delete resource by type and actual resource ID."""
        pass

    @abstractmethod
    def list_active_resources(
        self, resource_type: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[Resource]:
        """List active resources with pagination."""
        pass

    @abstractmethod
    def count_user_resources(
        self, user_id: UUID, resource_type: Optional[str] = None
    ) -> int:
        """Count resources owned by a user."""
        pass

    @abstractmethod
    def transfer_ownership(
        self, resource_type: str, resource_id: UUID, new_owner_id: UUID
    ) -> bool:
        """Transfer resource ownership."""
        pass
