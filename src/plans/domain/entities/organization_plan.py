from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"


class OrganizationPlan(BaseModel):
    id: UUID
    organization_id: UUID
    plan_id: UUID
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    feature_overrides: Dict[str, Any]  # Custom feature configurations
    limit_overrides: Dict[str, int]  # Custom limits
    started_at: datetime
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    auto_renew: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        plan_id: UUID,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        trial_days: int = 0,
        feature_overrides: Optional[Dict[str, Any]] = None,
        limit_overrides: Optional[Dict[str, int]] = None,
    ) -> "OrganizationPlan":
        now = datetime.utcnow()

        # Calculate expiration based on billing cycle
        if billing_cycle == BillingCycle.MONTHLY:
            expires_at = now + timedelta(days=30)
        elif billing_cycle == BillingCycle.YEARLY:
            expires_at = now + timedelta(days=365)
        else:  # LIFETIME
            expires_at = None

        # Set trial period if specified
        trial_ends_at = None
        if trial_days > 0:
            trial_ends_at = now + timedelta(days=trial_days)

        return cls(
            id=uuid4(),
            organization_id=organization_id,
            plan_id=plan_id,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=billing_cycle,
            feature_overrides=feature_overrides or {},
            limit_overrides=limit_overrides or {},
            started_at=now,
            expires_at=expires_at,
            trial_ends_at=trial_ends_at,
            auto_renew=True,
            created_at=now,
        )

    def renew(self, periods: int = 1) -> "OrganizationPlan":
        """Renew subscription for specified periods."""
        if self.billing_cycle == BillingCycle.LIFETIME:
            return self  # Lifetime subscriptions don't need renewal

        if not self.expires_at:
            raise ValueError("Cannot renew subscription without expiration date")

        days_per_period = 30 if self.billing_cycle == BillingCycle.MONTHLY else 365
        new_expires_at = self.expires_at + timedelta(days=days_per_period * periods)

        return self.model_copy(
            update={
                "expires_at": new_expires_at,
                "status": SubscriptionStatus.ACTIVE,
                "cancelled_at": None,
                "suspended_at": None,
                "updated_at": datetime.utcnow(),
            }
        )

    def cancel(self, immediate: bool = False) -> "OrganizationPlan":
        """Cancel subscription."""
        now = datetime.utcnow()

        updates = {"cancelled_at": now, "auto_renew": False, "updated_at": now}

        if immediate:
            updates["status"] = SubscriptionStatus.CANCELLED
            updates["expires_at"] = now

        return self.model_copy(update=updates)

    def suspend(self, reason: str = "") -> "OrganizationPlan":
        """Suspend subscription."""
        return self.model_copy(
            update={
                "status": SubscriptionStatus.SUSPENDED,
                "suspended_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

    def reactivate(self) -> "OrganizationPlan":
        """Reactivate suspended subscription."""
        if self.status != SubscriptionStatus.SUSPENDED:
            raise ValueError("Can only reactivate suspended subscriptions")

        return self.model_copy(
            update={
                "status": SubscriptionStatus.ACTIVE,
                "suspended_at": None,
                "updated_at": datetime.utcnow(),
            }
        )

    def set_feature_override(self, feature_name: str, value: Any) -> "OrganizationPlan":
        """Set custom feature configuration."""
        new_overrides = self.feature_overrides.copy()
        new_overrides[feature_name] = value

        return self.model_copy(
            update={"feature_overrides": new_overrides, "updated_at": datetime.utcnow()}
        )

    def remove_feature_override(self, feature_name: str) -> "OrganizationPlan":
        """Remove custom feature configuration."""
        new_overrides = self.feature_overrides.copy()
        new_overrides.pop(feature_name, None)

        return self.model_copy(
            update={"feature_overrides": new_overrides, "updated_at": datetime.utcnow()}
        )

    def set_limit_override(self, limit_name: str, value: int) -> "OrganizationPlan":
        """Set custom limit."""
        new_overrides = self.limit_overrides.copy()
        new_overrides[limit_name] = value

        return self.model_copy(
            update={"limit_overrides": new_overrides, "updated_at": datetime.utcnow()}
        )

    def remove_limit_override(self, limit_name: str) -> "OrganizationPlan":
        """Remove custom limit."""
        new_overrides = self.limit_overrides.copy()
        new_overrides.pop(limit_name, None)

        return self.model_copy(
            update={"limit_overrides": new_overrides, "updated_at": datetime.utcnow()}
        )

    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return self.status == SubscriptionStatus.ACTIVE

    def is_expired(self) -> bool:
        """Check if subscription has expired."""
        if not self.expires_at:
            return False  # Lifetime subscriptions don't expire

        return datetime.utcnow() > self.expires_at

    def is_in_trial(self) -> bool:
        """Check if subscription is in trial period."""
        if not self.trial_ends_at:
            return False

        return datetime.utcnow() <= self.trial_ends_at

    def is_cancelled(self) -> bool:
        """Check if subscription is cancelled."""
        return self.cancelled_at is not None

    def is_suspended(self) -> bool:
        """Check if subscription is suspended."""
        return self.status == SubscriptionStatus.SUSPENDED

    def days_until_expiry(self) -> Optional[int]:
        """Get days until subscription expires."""
        if not self.expires_at:
            return None

        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    def days_in_trial_remaining(self) -> Optional[int]:
        """Get days remaining in trial period."""
        if not self.trial_ends_at:
            return None

        delta = self.trial_ends_at - datetime.utcnow()
        return max(0, delta.days)

    def needs_renewal(self, days_ahead: int = 7) -> bool:
        """Check if subscription needs renewal within specified days."""
        if not self.expires_at or not self.auto_renew:
            return False

        renewal_date = datetime.utcnow() + timedelta(days=days_ahead)
        return renewal_date >= self.expires_at

    def get_effective_feature_value(self, feature_name: str, plan_default: Any) -> Any:
        """Get effective feature value considering overrides."""
        return self.feature_overrides.get(feature_name, plan_default)

    def get_effective_limit_value(self, limit_name: str, plan_default: int) -> int:
        """Get effective limit value considering overrides."""
        return self.limit_overrides.get(limit_name, plan_default)
