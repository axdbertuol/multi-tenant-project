from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"
    SUSPENDED = "suspended"


class BillingCycle(str, Enum):
    """Billing cycle enumeration."""

    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"
    WEEKLY = "weekly"


class Subscription(BaseModel):
    """Subscription domain entity."""

    id: UUID
    organization_id: UUID
    plan_id: UUID
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    starts_at: datetime
    ends_at: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        plan_id: UUID,
        billing_cycle: BillingCycle,
        starts_at: Optional[datetime] = None,
        ends_at: Optional[datetime] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "Subscription":
        """Create a new subscription."""
        now = datetime.utcnow()
        start_date = starts_at or now

        return cls(
            id=uuid4(),
            organization_id=organization_id,
            plan_id=plan_id,
            status=SubscriptionStatus.PENDING,
            billing_cycle=billing_cycle,
            starts_at=start_date,
            ends_at=ends_at,
            next_billing_date=cls._calculate_next_billing_date(
                start_date, billing_cycle
            ),
            metadata=metadata or {},
            created_at=now,
        )

    def activate(self) -> "Subscription":
        """Activate the subscription."""
        if self.status == SubscriptionStatus.ACTIVE:
            return self

        return self.model_copy(
            update={
                "status": SubscriptionStatus.ACTIVE,
                "updated_at": datetime.utcnow(),
            }
        )

    def cancel(self, cancellation_reason: Optional[str] = None) -> "Subscription":
        """Cancel the subscription."""
        cancelled_at = datetime.utcnow()
        metadata = self.metadata.copy()

        if cancellation_reason:
            metadata["cancellation_reason"] = cancellation_reason

        return self.model_copy(
            update={
                "status": SubscriptionStatus.CANCELLED,
                "cancelled_at": cancelled_at,
                "metadata": metadata,
                "updated_at": cancelled_at,
            }
        )

    def suspend(self, reason: Optional[str] = None) -> "Subscription":
        """Suspend the subscription."""
        metadata = self.metadata.copy()
        if reason:
            metadata["suspension_reason"] = reason

        return self.model_copy(
            update={
                "status": SubscriptionStatus.SUSPENDED,
                "metadata": metadata,
                "updated_at": datetime.utcnow(),
            }
        )

    def reactivate(self) -> "Subscription":
        """Reactivate a suspended subscription."""
        if self.status not in [
            SubscriptionStatus.SUSPENDED,
            SubscriptionStatus.INACTIVE,
        ]:
            raise ValueError("Can only reactivate suspended or inactive subscriptions")

        metadata = self.metadata.copy()
        metadata.pop("suspension_reason", None)

        return self.model_copy(
            update={
                "status": SubscriptionStatus.ACTIVE,
                "metadata": metadata,
                "updated_at": datetime.utcnow(),
            }
        )

    def expire(self) -> "Subscription":
        """Mark subscription as expired."""
        return self.model_copy(
            update={
                "status": SubscriptionStatus.EXPIRED,
                "updated_at": datetime.utcnow(),
            }
        )

    def change_plan(self, new_plan_id: UUID) -> "Subscription":
        """Change the subscription plan."""
        return self.model_copy(
            update={
                "plan_id": new_plan_id,
                "updated_at": datetime.utcnow(),
            }
        )

    def change_billing_cycle(self, new_billing_cycle: BillingCycle) -> "Subscription":
        """Change the billing cycle."""
        new_next_billing = self._calculate_next_billing_date(
            self.next_billing_date or datetime.utcnow(), new_billing_cycle
        )

        return self.model_copy(
            update={
                "billing_cycle": new_billing_cycle,
                "next_billing_date": new_next_billing,
                "updated_at": datetime.utcnow(),
            }
        )

    def extend(self, new_end_date: datetime) -> "Subscription":
        """Extend the subscription end date."""
        if new_end_date <= (self.ends_at or datetime.utcnow()):
            raise ValueError("New end date must be after current end date")

        return self.model_copy(
            update={
                "ends_at": new_end_date,
                "updated_at": datetime.utcnow(),
            }
        )

    def update_next_billing_date(self, next_billing_date: datetime) -> "Subscription":
        """Update the next billing date."""
        return self.model_copy(
            update={
                "next_billing_date": next_billing_date,
                "updated_at": datetime.utcnow(),
            }
        )

    def add_metadata(self, key: str, value: Any) -> "Subscription":
        """Add or update metadata."""
        metadata = self.metadata.copy()
        metadata[key] = value

        return self.model_copy(
            update={
                "metadata": metadata,
                "updated_at": datetime.utcnow(),
            }
        )

    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        if self.status != SubscriptionStatus.ACTIVE:
            return False

        if self.ends_at and datetime.utcnow() > self.ends_at:
            return False

        return True

    def is_expired(self) -> bool:
        """Check if subscription has expired."""
        if self.status == SubscriptionStatus.EXPIRED:
            return True

        if self.ends_at and datetime.utcnow() > self.ends_at:
            return True

        return False

    def is_cancelled(self) -> bool:
        """Check if subscription is cancelled."""
        return self.status == SubscriptionStatus.CANCELLED

    def is_trial(self) -> bool:
        """Check if subscription is a trial."""
        return self.status == SubscriptionStatus.TRIAL

    def days_until_expiry(self) -> Optional[int]:
        """Get days until subscription expires."""
        if not self.ends_at:
            return None

        delta = self.ends_at - datetime.utcnow()
        return max(0, delta.days)

    def days_since_created(self) -> int:
        """Get days since subscription was created."""
        delta = datetime.utcnow() - self.created_at
        return delta.days

    def can_be_cancelled(self) -> bool:
        """Check if subscription can be cancelled."""
        return self.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIAL,
            SubscriptionStatus.SUSPENDED,
        ]

    def can_be_upgraded(self) -> bool:
        """Check if subscription can be upgraded."""
        return self.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIAL,
        ]

    def can_be_downgraded(self) -> bool:
        """Check if subscription can be downgraded."""
        return self.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIAL,
        ]

    @staticmethod
    def _calculate_next_billing_date(
        start_date: datetime, billing_cycle: BillingCycle
    ) -> datetime:
        """Calculate next billing date based on billing cycle."""
        from datetime import timedelta

        if billing_cycle == BillingCycle.MONTHLY:
            # Approximate month as 30 days
            return start_date + timedelta(days=30)
        elif billing_cycle == BillingCycle.YEARLY:
            return start_date + timedelta(days=365)
        elif billing_cycle == BillingCycle.QUARTERLY:
            return start_date + timedelta(days=90)
        elif billing_cycle == BillingCycle.WEEKLY:
            return start_date + timedelta(weeks=1)
        else:
            raise ValueError(f"Unsupported billing cycle: {billing_cycle}")
