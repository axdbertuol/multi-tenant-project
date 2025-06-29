from typing import Optional, Dict, Any, List
from uuid import UUID

from ..entities.organization_plan import (
    OrganizationPlan,
    BillingCycle,
)
from ..entities.plan import Plan
from ..repositories.organization_plan_repository import OrganizationPlanRepository
from ..repositories.plan_repository import PlanRepository


class SubscriptionService:
    """Domain service for managing organization plan subscriptions."""

    def __init__(
        self,
        org_plan_repository: OrganizationPlanRepository,
        plan_repository: PlanRepository,
    ):
        self._org_plan_repository = org_plan_repository
        self._plan_repository = plan_repository

    def subscribe_organization_to_plan(
        self,
        organization_id: UUID,
        plan_id: UUID,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        trial_days: int = 0,
        feature_overrides: Optional[Dict[str, Any]] = None,
        limit_overrides: Optional[Dict[str, int]] = None,
    ) -> OrganizationPlan:
        """Subscribe organization to a plan."""

        # Validate plan exists and is available
        plan = self._plan_repository.get_by_id(plan_id)
        if not plan:
            raise ValueError("Plan not found")

        if not plan.is_available_for_signup():
            raise ValueError("Plan is not available for signup")

        # Check if organization already has an active subscription
        existing_subscription = self._org_plan_repository.get_by_organization_id(
            organization_id
        )

        if existing_subscription and existing_subscription.is_active():
            raise ValueError("Organization already has an active subscription")

        # Create new subscription
        org_plan = OrganizationPlan.create(
            organization_id=organization_id,
            plan_id=plan_id,
            billing_cycle=billing_cycle,
            trial_days=trial_days,
            feature_overrides=feature_overrides,
            limit_overrides=limit_overrides,
        )

        return self._org_plan_repository.save(org_plan)

    def upgrade_organization_plan(
        self,
        organization_id: UUID,
        new_plan_id: UUID,
        effective_immediately: bool = True,
    ) -> OrganizationPlan:
        """Upgrade organization to a different plan."""

        current_subscription = self._org_plan_repository.get_by_organization_id(
            organization_id
        )
        if not current_subscription:
            raise ValueError("Organization has no active subscription")

        if not current_subscription.is_active():
            raise ValueError("Current subscription is not active")

        new_plan = self._plan_repository.get_by_id(new_plan_id)
        if not new_plan:
            raise ValueError("New plan not found")

        if not new_plan.is_available_for_signup():
            raise ValueError("New plan is not available")

        # Cancel current subscription
        cancelled_subscription = current_subscription.cancel(
            immediate=effective_immediately
        )
        self._org_plan_repository.save(cancelled_subscription)

        # Create new subscription with same billing cycle
        new_subscription = OrganizationPlan.create(
            organization_id=organization_id,
            plan_id=new_plan_id,
            billing_cycle=current_subscription.billing_cycle,
            feature_overrides=current_subscription.feature_overrides,
            limit_overrides=current_subscription.limit_overrides,
        )

        return self._org_plan_repository.save(new_subscription)

    def cancel_subscription(
        self, organization_id: UUID, immediate: bool = False, reason: str = ""
    ) -> OrganizationPlan:
        """Cancel organization subscription."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            raise ValueError("Organization has no subscription")

        if subscription.is_cancelled():
            raise ValueError("Subscription is already cancelled")

        cancelled_subscription = subscription.cancel(immediate=immediate)
        return self._org_plan_repository.save(cancelled_subscription)

    def renew_subscription(
        self, organization_id: UUID, periods: int = 1
    ) -> OrganizationPlan:
        """Renew organization subscription."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            raise ValueError("Organization has no subscription")

        renewed_subscription = subscription.renew(periods)
        return self._org_plan_repository.save(renewed_subscription)

    def suspend_subscription(
        self, organization_id: UUID, reason: str = ""
    ) -> OrganizationPlan:
        """Suspend organization subscription."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            raise ValueError("Organization has no subscription")

        if not subscription.is_active():
            raise ValueError("Can only suspend active subscriptions")

        suspended_subscription = subscription.suspend(reason)
        return self._org_plan_repository.save(suspended_subscription)

    def reactivate_subscription(self, organization_id: UUID) -> OrganizationPlan:
        """Reactivate suspended subscription."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            raise ValueError("Organization has no subscription")

        reactivated_subscription = subscription.reactivate()
        return self._org_plan_repository.save(reactivated_subscription)

    def apply_feature_override(
        self, organization_id: UUID, feature_name: str, value: Any
    ) -> OrganizationPlan:
        """Apply custom feature configuration to organization."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            raise ValueError("Organization has no subscription")

        updated_subscription = subscription.set_feature_override(feature_name, value)
        return self._org_plan_repository.save(updated_subscription)

    def apply_limit_override(
        self, organization_id: UUID, limit_name: str, value: int
    ) -> OrganizationPlan:
        """Apply custom limit to organization."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            raise ValueError("Organization has no subscription")

        updated_subscription = subscription.set_limit_override(limit_name, value)
        return self._org_plan_repository.save(updated_subscription)

    def get_organization_plan_details(
        self, organization_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get comprehensive plan details for organization."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            return None

        plan = self._plan_repository.get_by_id(subscription.plan_id)
        if not plan:
            return None

        return {
            "subscription_id": str(subscription.id),
            "plan": {
                "id": str(plan.id),
                "name": plan.name.value,
                "type": plan.plan_type.value,
                "description": plan.description,
            },
            "status": subscription.status.value,
            "billing_cycle": subscription.billing_cycle.value,
            "started_at": subscription.started_at.isoformat(),
            "expires_at": subscription.expires_at.isoformat()
            if subscription.expires_at
            else None,
            "trial_ends_at": subscription.trial_ends_at.isoformat()
            if subscription.trial_ends_at
            else None,
            "auto_renew": subscription.auto_renew,
            "is_active": subscription.is_active(),
            "is_expired": subscription.is_expired(),
            "is_in_trial": subscription.is_in_trial(),
            "is_cancelled": subscription.is_cancelled(),
            "days_until_expiry": subscription.days_until_expiry(),
            "days_in_trial_remaining": subscription.days_in_trial_remaining(),
            "needs_renewal": subscription.needs_renewal(),
            "feature_overrides": subscription.feature_overrides,
            "limit_overrides": subscription.limit_overrides,
            "effective_features": self._get_effective_features(plan, subscription),
            "effective_limits": self._get_effective_limits(plan, subscription),
        }

    def _get_effective_features(
        self, plan: Plan, subscription: OrganizationPlan
    ) -> Dict[str, Any]:
        """Get effective feature configuration considering overrides."""
        effective_features = plan.features.copy()
        effective_features.update(subscription.feature_overrides)
        return effective_features

    def _get_effective_limits(
        self, plan: Plan, subscription: OrganizationPlan
    ) -> Dict[str, int]:
        """Get effective limits considering overrides."""
        effective_limits = plan.limits.copy()
        effective_limits.update(subscription.limit_overrides)
        return effective_limits

    def get_subscriptions_requiring_renewal(
        self, days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """Get subscriptions that need renewal soon."""
        expiring_plans = self._org_plan_repository.get_expiring_plans(days_ahead)

        renewal_list = []
        for subscription in expiring_plans:
            if subscription.auto_renew and subscription.is_active():
                plan = self._plan_repository.get_by_id(subscription.plan_id)

                renewal_list.append(
                    {
                        "organization_id": str(subscription.organization_id),
                        "subscription_id": str(subscription.id),
                        "plan_name": plan.name.value if plan else "Unknown",
                        "expires_at": subscription.expires_at.isoformat()
                        if subscription.expires_at
                        else None,
                        "days_until_expiry": subscription.days_until_expiry(),
                        "billing_cycle": subscription.billing_cycle.value,
                    }
                )

        return renewal_list

    def get_trial_ending_soon(self, days_ahead: int = 3) -> List[Dict[str, Any]]:
        """Get subscriptions with trials ending soon."""
        trial_ending = self._org_plan_repository.get_trial_ending_plans(days_ahead)

        ending_list = []
        for subscription in trial_ending:
            if subscription.is_in_trial() and subscription.is_active():
                plan = self._plan_repository.get_by_id(subscription.plan_id)

                ending_list.append(
                    {
                        "organization_id": str(subscription.organization_id),
                        "subscription_id": str(subscription.id),
                        "plan_name": plan.name.value if plan else "Unknown",
                        "trial_ends_at": subscription.trial_ends_at.isoformat()
                        if subscription.trial_ends_at
                        else None,
                        "days_in_trial_remaining": subscription.days_in_trial_remaining(),
                    }
                )

        return ending_list
