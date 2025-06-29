from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ..entities.organization_plan import OrganizationPlan, SubscriptionStatus


class OrganizationPlanRepository(ABC):
    """Organization plan repository interface for the Plans bounded context."""

    @abstractmethod
    def save(self, organization_plan: OrganizationPlan) -> OrganizationPlan:
        """Save or update an organization plan."""
        pass

    @abstractmethod
    def get_by_id(self, organization_plan_id: UUID) -> Optional[OrganizationPlan]:
        """Get organization plan by ID."""
        pass

    @abstractmethod
    def get_by_organization_id(
        self, organization_id: UUID
    ) -> Optional[OrganizationPlan]:
        """Get current plan for an organization."""
        pass

    @abstractmethod
    def get_organization_plan_history(
        self, organization_id: UUID
    ) -> List[OrganizationPlan]:
        """Get plan history for an organization."""
        pass

    @abstractmethod
    def get_by_plan_id(self, plan_id: UUID) -> List[OrganizationPlan]:
        """Get all organizations using a specific plan."""
        pass

    @abstractmethod
    def get_expiring_plans(self, days_ahead: int = 7) -> List[OrganizationPlan]:
        """Get plans expiring within specified days."""
        pass

    @abstractmethod
    def get_trial_ending_plans(self, days_ahead: int = 3) -> List[OrganizationPlan]:
        """Get plans with trials ending within specified days."""
        pass

    @abstractmethod
    def get_by_status(self, status: SubscriptionStatus) -> List[OrganizationPlan]:
        """Get organization plans by status."""
        pass

    @abstractmethod
    def delete(self, organization_plan_id: UUID) -> bool:
        """Delete organization plan by ID."""
        pass

    @abstractmethod
    def count_active_subscriptions(self, plan_id: Optional[UUID] = None) -> int:
        """Count active subscriptions, optionally filtered by plan."""
        pass

    @abstractmethod
    def get_organizations_with_feature(
        self, feature_name: str, enabled: bool = True
    ) -> List[UUID]:
        """Get organization IDs that have a specific feature enabled/disabled."""
        pass

    @abstractmethod
    def cleanup_expired_plans(self) -> int:
        """Update status of expired plans. Returns count of updated plans."""
        pass
