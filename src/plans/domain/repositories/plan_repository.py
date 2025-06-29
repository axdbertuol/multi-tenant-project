from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.plan import Plan, PlanType, PlanStatus
from ..value_objects.plan_name import PlanName


class PlanRepository(ABC):
    """Plan repository interface for the Plans bounded context."""

    @abstractmethod
    def save(self, plan: Plan) -> Plan:
        """Save or update a plan."""
        pass

    @abstractmethod
    def get_by_id(self, plan_id: UUID) -> Optional[Plan]:
        """Get plan by ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: PlanName) -> Optional[Plan]:
        """Get plan by name."""
        pass

    @abstractmethod
    def get_by_type(self, plan_type: PlanType) -> List[Plan]:
        """Get plans by type."""
        pass

    @abstractmethod
    def get_public_plans(self) -> List[Plan]:
        """Get all public plans available for signup."""
        pass

    @abstractmethod
    def get_active_plans(self) -> List[Plan]:
        """Get all active plans."""
        pass

    @abstractmethod
    def exists_by_name(self, name: PlanName) -> bool:
        """Check if plan exists by name."""
        pass

    @abstractmethod
    def delete(self, plan_id: UUID) -> bool:
        """Delete plan by ID."""
        pass

    @abstractmethod
    def list_plans(
        self,
        status: Optional[PlanStatus] = None,
        is_public: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Plan]:
        """List plans with filtering and pagination."""
        pass

    @abstractmethod
    def count_plans(self, status: Optional[PlanStatus] = None) -> int:
        """Count plans by status."""
        pass

    @abstractmethod
    def get_plans_with_resource(self, resource_type: str) -> List[Plan]:
        """Get plans that have a specific resource enabled."""
        pass

    @abstractmethod
    def assign_to_organization(self, plan_id: UUID, organization_id: UUID) -> bool:
        """Assign plan to organization."""
        pass

    @abstractmethod
    def validate_plan_resources(self, plan_id: UUID) -> tuple[bool, List[str]]:
        """Validate that plan resources have required configurations."""
        pass

    @abstractmethod
    def get_plans_requiring_api_key(self, api_key_name: str) -> List[Plan]:
        """Get plans that require a specific API key."""
        pass
