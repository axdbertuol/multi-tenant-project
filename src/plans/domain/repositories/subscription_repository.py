from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from ..entities.subscription import Subscription


class SubscriptionRepository(ABC):
    """Abstract repository for Subscription entities."""

    @abstractmethod
    def save(self, subscription: Subscription) -> Subscription:
        """Save a subscription entity."""
        pass

    @abstractmethod
    def find_by_id(self, subscription_id: UUID) -> Optional[Subscription]:
        """Find a subscription by ID."""
        pass

    @abstractmethod
    def find_by_organization(self, organization_id: UUID) -> List[Subscription]:
        """Find all subscriptions for an organization."""
        pass

    @abstractmethod
    def find_active_by_organization(
        self, organization_id: UUID
    ) -> Optional[Subscription]:
        """Find active subscription for an organization."""
        pass

    @abstractmethod
    def find_by_plan(self, plan_id: UUID) -> List[Subscription]:
        """Find all subscriptions for a plan."""
        pass

    @abstractmethod
    def find_by_status(self, status: str) -> List[Subscription]:
        """Find subscriptions by status."""
        pass

    @abstractmethod
    def find_expiring_before(self, date: datetime) -> List[Subscription]:
        """Find subscriptions expiring before a date."""
        pass

    @abstractmethod
    def find_due_for_billing(self, date: datetime) -> List[Subscription]:
        """Find subscriptions due for billing."""
        pass

    @abstractmethod
    def find_paginated(
        self,
        organization_id: Optional[UUID] = None,
        plan_id: Optional[UUID] = None,
        status: Optional[str] = None,
        billing_cycle: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Subscription], int]:
        """Find subscriptions with pagination and filters.

        Returns:
            Tuple of (subscriptions, total_count)
        """
        pass

    @abstractmethod
    def delete(self, subscription_id: UUID) -> bool:
        """Delete a subscription (hard delete).

        Returns:
            True if subscription was deleted, False if not found
        """
        pass

    @abstractmethod
    def update_status(self, subscription_id: UUID, status: str) -> bool:
        """Update subscription status.

        Returns:
            True if subscription was updated, False if not found
        """
        pass

    @abstractmethod
    def cancel_subscription(
        self,
        subscription_id: UUID,
        cancelled_at: datetime,
        cancellation_reason: Optional[str] = None,
    ) -> bool:
        """Cancel a subscription.

        Args:
            subscription_id: ID of subscription to cancel
            cancelled_at: Timestamp when subscription was cancelled
            cancellation_reason: Optional reason for cancellation

        Returns:
            True if subscription was cancelled, False if not found
        """
        pass

    @abstractmethod
    def update_billing_date(
        self, subscription_id: UUID, next_billing_date: datetime
    ) -> bool:
        """Update subscription billing date.

        Returns:
            True if subscription was updated, False if not found
        """
        pass

    @abstractmethod
    def extend_subscription(
        self, subscription_id: UUID, new_end_date: datetime
    ) -> bool:
        """Extend subscription end date.

        Returns:
            True if subscription was extended, False if not found
        """
        pass

    @abstractmethod
    def change_plan(self, subscription_id: UUID, new_plan_id: UUID) -> bool:
        """Change subscription plan.

        Returns:
            True if plan was changed, False if not found
        """
        pass

    @abstractmethod
    def get_active_subscriptions_count(self) -> int:
        """Get count of active subscriptions."""
        pass

    @abstractmethod
    def get_revenue_by_period(self, start_date: datetime, end_date: datetime) -> dict:
        """Get revenue data for a period.

        Returns:
            Dictionary with revenue metrics for the period
        """
        pass
