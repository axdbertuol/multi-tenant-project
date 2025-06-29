from typing import Dict, Any, List, Optional
from uuid import UUID

from ..entities.feature_usage import FeatureUsage, UsagePeriod
from ..repositories.feature_usage_repository import FeatureUsageRepository
from ..repositories.organization_plan_repository import OrganizationPlanRepository
from ..repositories.plan_repository import PlanRepository


class UsageTrackingService:
    """Domain service for tracking and managing feature usage."""

    def __init__(
        self,
        usage_repository: FeatureUsageRepository,
        org_plan_repository: OrganizationPlanRepository,
        plan_repository: PlanRepository,
    ):
        self._usage_repository = usage_repository
        self._org_plan_repository = org_plan_repository
        self._plan_repository = plan_repository

    def track_feature_usage(
        self,
        organization_id: UUID,
        feature_name: str,
        amount: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, str, Optional[FeatureUsage]]:
        """Track feature usage and validate against limits."""

        # Get organization subscription and plan
        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription or not subscription.is_active():
            return False, "Organization has no active subscription", None

        plan = self._plan_repository.get_by_id(subscription.plan_id)
        if not plan:
            return False, "Plan not found", None

        # Check if feature is enabled
        effective_feature_value = subscription.get_effective_feature_value(
            feature_name, plan.get_feature_config(feature_name)
        )

        if not effective_feature_value:
            return False, f"Feature '{feature_name}' is not enabled for this plan", None

        # Get current usage
        current_usage = self._usage_repository.get_current_usage(
            organization_id, feature_name, UsagePeriod.MONTHLY
        )

        # Create usage record if doesn't exist
        if not current_usage:
            limit_value = subscription.get_effective_limit_value(
                f"monthly_{feature_name}", plan.get_limit(f"monthly_{feature_name}")
            )

            current_usage = FeatureUsage.create(
                organization_id=organization_id,
                feature_name=feature_name,
                usage_period=UsagePeriod.MONTHLY,
                limit_value=limit_value,
            )
            current_usage = self._usage_repository.save(current_usage)

        # Check if usage would exceed limit
        can_use, reason = current_usage.can_use_feature(amount)
        if not can_use:
            return False, reason, current_usage

        # Increment usage
        updated_usage = self._usage_repository.increment_usage(
            organization_id, feature_name, amount, metadata
        )

        return True, "Usage tracked successfully", updated_usage

    def get_organization_usage_summary(self, organization_id: UUID) -> Dict[str, Any]:
        """Get comprehensive usage summary for organization."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            return {"error": "No active subscription found"}

        plan = self._plan_repository.get_by_id(subscription.plan_id)
        if not plan:
            return {"error": "Plan not found"}

        # Get current usage for all features
        usage_records = self._usage_repository.get_organization_usage(organization_id)

        summary = {
            "organization_id": str(organization_id),
            "plan": {"name": plan.name.value, "type": plan.plan_type.value},
            "billing_period": {
                "cycle": subscription.billing_cycle.value,
                "started_at": subscription.started_at.isoformat(),
                "expires_at": subscription.expires_at.isoformat()
                if subscription.expires_at
                else None,
            },
            "features": {},
            "overall_status": "healthy",
        }

        # Process each usage record
        for usage in usage_records:
            if usage.is_current_period():
                feature_summary = usage.get_usage_summary()
                summary["features"][usage.feature_name] = feature_summary

                # Update overall status based on usage
                if usage.is_limit_exceeded():
                    summary["overall_status"] = "over_limit"
                elif usage.is_limit_near() and summary["overall_status"] == "healthy":
                    summary["overall_status"] = "approaching_limit"

        return summary

    def check_feature_access(
        self, organization_id: UUID, feature_name: str, requested_amount: int = 1
    ) -> tuple[bool, str, Dict[str, Any]]:
        """Check if organization can use a feature."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription or not subscription.is_active():
            return False, "No active subscription", {}

        plan = self._plan_repository.get_by_id(subscription.plan_id)
        if not plan:
            return False, "Plan not found", {}

        # Check if feature is enabled in plan
        effective_feature_value = subscription.get_effective_feature_value(
            feature_name, plan.get_feature_config(feature_name)
        )

        if not effective_feature_value:
            return (
                False,
                f"Feature '{feature_name}' not available in current plan",
                {"upgrade_required": True, "current_plan": plan.name.value},
            )

        # Check usage limits
        current_usage = self._usage_repository.get_current_usage(
            organization_id, feature_name, UsagePeriod.MONTHLY
        )

        if current_usage:
            can_use, reason = current_usage.can_use_feature(requested_amount)

            if not can_use:
                return (
                    False,
                    reason,
                    {
                        "current_usage": current_usage.current_usage,
                        "limit": current_usage.limit_value,
                        "usage_percentage": current_usage.get_usage_percentage(),
                        "days_until_reset": current_usage.days_until_reset(),
                        "upgrade_recommended": current_usage.is_limit_near(0.9),
                    },
                )

        return (
            True,
            "Feature access granted",
            {
                "remaining_usage": current_usage.get_remaining_usage()
                if current_usage
                else -1
            },
        )

    def get_usage_analytics(
        self, organization_id: UUID, feature_name: str, periods: int = 12
    ) -> Dict[str, Any]:
        """Get usage analytics and trends."""

        trends = self._usage_repository.get_usage_trends(
            organization_id, feature_name, periods
        )

        current_usage = self._usage_repository.get_current_usage(
            organization_id, feature_name, UsagePeriod.MONTHLY
        )

        analytics = {
            "feature_name": feature_name,
            "trends": trends,
            "current_period": current_usage.get_usage_summary()
            if current_usage
            else None,
            "insights": [],
        }

        # Generate insights
        if trends and len(trends) > 1:
            # Calculate growth trend
            recent_usage = [t["usage"] for t in trends[-3:]]
            if len(recent_usage) >= 2:
                growth_rate = (
                    (recent_usage[-1] - recent_usage[0]) / max(recent_usage[0], 1) * 100
                )

                if growth_rate > 50:
                    analytics["insights"].append(
                        {
                            "type": "high_growth",
                            "message": f"Usage has grown by {growth_rate:.1f}% in recent periods",
                        }
                    )
                elif growth_rate < -20:
                    analytics["insights"].append(
                        {
                            "type": "declining_usage",
                            "message": f"Usage has declined by {abs(growth_rate):.1f}% in recent periods",
                        }
                    )

        # Add limit warnings
        if current_usage and current_usage.is_limit_near(0.8):
            analytics["insights"].append(
                {
                    "type": "approaching_limit",
                    "message": f"Currently at {current_usage.get_usage_percentage():.1f}% of monthly limit",
                }
            )

        return analytics

    def reset_monthly_usage(self, organization_id: UUID) -> Dict[str, int]:
        """Reset monthly usage for organization (typically called by scheduler)."""

        usage_records = self._usage_repository.get_organization_usage(organization_id)
        reset_counts = {}

        for usage in usage_records:
            if usage.usage_period == UsagePeriod.MONTHLY and usage.is_period_expired():
                reset_usage = self._usage_repository.reset_usage_for_period(
                    organization_id, usage.feature_name, UsagePeriod.MONTHLY
                )

                if reset_usage:
                    reset_counts[usage.feature_name] = usage.current_usage

        return reset_counts

    def get_organizations_near_limits(
        self, threshold_percent: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Get organizations approaching their usage limits."""

        near_limit_orgs = []

        # Get organizations exceeding threshold for various features
        feature_names = ["monthly_messages", "monthly_api_calls", "storage_mb"]

        for feature_name in feature_names:
            org_ids = self._usage_repository.get_organizations_exceeding_limit(
                feature_name, threshold_percent
            )

            for org_id in org_ids:
                usage = self._usage_repository.get_current_usage(
                    org_id, feature_name, UsagePeriod.MONTHLY
                )

                if usage:
                    near_limit_orgs.append(
                        {
                            "organization_id": str(org_id),
                            "feature_name": feature_name,
                            "usage_percentage": usage.get_usage_percentage(),
                            "current_usage": usage.current_usage,
                            "limit": usage.limit_value,
                            "days_until_reset": usage.days_until_reset(),
                        }
                    )

        return near_limit_orgs
