from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..entities.plan_resource import PlanResource, PlanResourceType


class PlanResourceRepository(ABC):
    """Plan resource repository interface for the Plans bounded context."""

    @abstractmethod
    def save(self, plan_resource: PlanResource) -> PlanResource:
        """Save or update a plan resource."""
        pass

    @abstractmethod
    def get_by_id(self, resource_id: UUID) -> Optional[PlanResource]:
        """Get plan resource by ID."""
        pass

    @abstractmethod
    def get_by_plan_id(self, plan_id: UUID) -> List[PlanResource]:
        """Get all resources for a plan."""
        pass

    @abstractmethod
    def get_by_plan_and_type(
        self, plan_id: UUID, resource_type: PlanResourceType
    ) -> Optional[PlanResource]:
        """Get specific resource type for a plan."""
        pass

    @abstractmethod
    def get_by_resource_type(
        self, resource_type: PlanResourceType
    ) -> List[PlanResource]:
        """Get all resources of a specific type."""
        pass

    @abstractmethod
    def get_active_resources(self, plan_id: UUID) -> List[PlanResource]:
        """Get all active resources for a plan."""
        pass

    @abstractmethod
    def delete(self, resource_id: UUID) -> bool:
        """Delete plan resource by ID."""
        pass

    @abstractmethod
    def delete_by_plan_id(self, plan_id: UUID) -> int:
        """Delete all resources for a plan. Returns count of deleted resources."""
        pass

    @abstractmethod
    def exists_by_plan_and_type(
        self, plan_id: UUID, resource_type: PlanResourceType
    ) -> bool:
        """Check if plan has specific resource type."""
        pass

    @abstractmethod
    def update_configuration(
        self, resource_id: UUID, configuration: Dict[str, Any]
    ) -> Optional[PlanResource]:
        """Update resource configuration."""
        pass

    @abstractmethod
    def activate_resource(self, resource_id: UUID) -> bool:
        """Activate a resource."""
        pass

    @abstractmethod
    def deactivate_resource(self, resource_id: UUID) -> bool:
        """Deactivate a resource."""
        pass

    @abstractmethod
    def list_resources(
        self,
        resource_type: Optional[PlanResourceType] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PlanResource]:
        """List plan resources with filtering and pagination."""
        pass

    @abstractmethod
    def count_resources(
        self,
        resource_type: Optional[PlanResourceType] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """Count plan resources with optional filtering."""
        pass

    @abstractmethod
    def get_resources_with_api_key(self, api_key_name: str) -> List[PlanResource]:
        """Get resources that have a specific API key configured."""
        pass

    @abstractmethod
    def validate_api_key_uniqueness(
        self,
        api_key_name: str,
        api_key_value: str,
        excluding_resource_id: Optional[UUID] = None,
    ) -> bool:
        """Check if API key value is unique across resources."""
        pass
