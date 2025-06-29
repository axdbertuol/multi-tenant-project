from typing import List, Dict, Any, Optional
from uuid import UUID
from decimal import Decimal

from ..entities.plan import Plan, PlanType
from ..entities.plan_feature import PlanFeature
from ..repositories.plan_repository import PlanRepository
from ..repositories.plan_feature_repository import PlanFeatureRepository
from ..repositories.organization_plan_repository import OrganizationPlanRepository
from ..value_objects.pricing import Pricing


class PlanManagementService:
    """Domain service for managing plans and features."""

    def __init__(
        self,
        plan_repository: PlanRepository,
        feature_repository: PlanFeatureRepository,
        org_plan_repository: OrganizationPlanRepository,
    ):
        self._plan_repository = plan_repository
        self._feature_repository = feature_repository
        self._org_plan_repository = org_plan_repository

    def create_standard_plans(self) -> List[Plan]:
        """Create standard system plans (Free, Basic, Premium, Enterprise)."""
        plans = []

        # Free Plan
        free_plan = Plan.create(
            name="Free",
            description="Basic features for getting started",
            plan_type=PlanType.FREE,
            pricing=Pricing.create_free(),
            max_users=5,
            max_organizations=1,
        )
        plans.append(self._plan_repository.save(free_plan))

        # Basic Plan
        basic_plan = Plan.create(
            name="Basic",
            description="Essential features for small teams",
            plan_type=PlanType.BASIC,
            pricing=Pricing.create_per_user(
                base_amount=Decimal("29.00"),
                per_user_amount=Decimal("5.00"),
                free_user_count=2,
            ),
            max_users=25,
            max_organizations=3,
        )
        plans.append(self._plan_repository.save(basic_plan))

        # Premium Plan
        premium_plan = Plan.create(
            name="Premium",
            description="Advanced features for growing businesses",
            plan_type=PlanType.PREMIUM,
            pricing=Pricing.create_per_user(
                base_amount=Decimal("79.00"),
                per_user_amount=Decimal("8.00"),
                free_user_count=5,
            ),
            max_users=100,
            max_organizations=10,
        )
        plans.append(self._plan_repository.save(premium_plan))

        # Enterprise Plan
        enterprise_plan = Plan.create(
            name="Enterprise",
            description="Full features for large organizations",
            plan_type=PlanType.ENTERPRISE,
            pricing=Pricing.create_per_user(
                base_amount=Decimal("199.00"),
                per_user_amount=Decimal("12.00"),
                free_user_count=10,
            ),
            max_users=1000,
            max_organizations=50,
        )
        plans.append(self._plan_repository.save(enterprise_plan))

        return plans

    def create_system_features(self) -> List[PlanFeature]:
        """Create standard system features."""
        features = []

        # Create WhatsApp chat feature
        whatsapp_feature = PlanFeature.create_chat_whatsapp_feature()
        features.append(self._feature_repository.save(whatsapp_feature))

        # Create iframe chat feature
        iframe_feature = PlanFeature.create_chat_iframe_feature()
        features.append(self._feature_repository.save(iframe_feature))

        return features

    def can_plan_be_deleted(self, plan_id: UUID) -> tuple[bool, str]:
        """Check if plan can be safely deleted."""
        plan = self._plan_repository.get_by_id(plan_id)

        if not plan:
            return False, "Plan not found"

        # Check if plan has active subscriptions
        active_subscriptions = self._org_plan_repository.count_active_subscriptions(
            plan_id
        )

        if active_subscriptions > 0:
            return (
                False,
                f"Plan has {active_subscriptions} active subscriptions and cannot be deleted",
            )

        return True, "Plan can be deleted"

    def validate_plan_upgrade(
        self, current_plan_id: UUID, target_plan_id: UUID, organization_users: int
    ) -> tuple[bool, str]:
        """Validate if organization can upgrade to target plan."""
        current_plan = self._plan_repository.get_by_id(current_plan_id)
        target_plan = self._plan_repository.get_by_id(target_plan_id)

        if not current_plan:
            return False, "Current plan not found"

        if not target_plan:
            return False, "Target plan not found"

        if not target_plan.is_available_for_signup():
            return False, "Target plan is not available for signup"

        # Check if target plan can support current user count
        if not target_plan.can_support_users(organization_users):
            return (
                False,
                f"Target plan supports max {target_plan.max_users} users, but organization has {organization_users}",
            )

        # Prevent downgrade (optional business rule)
        plan_hierarchy = {
            PlanType.FREE: 0,
            PlanType.BASIC: 1,
            PlanType.PREMIUM: 2,
            PlanType.ENTERPRISE: 3,
        }

        current_level = plan_hierarchy.get(current_plan.plan_type, 0)
        target_level = plan_hierarchy.get(target_plan.plan_type, 0)

        if target_level < current_level:
            return False, "Downgrading plans is not allowed. Please contact support."

        return True, "Plan upgrade is valid"

    def calculate_plan_cost_comparison(
        self, plan_ids: List[UUID], user_count: int = 1
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate and compare costs for multiple plans."""
        comparison = {}

        for plan_id in plan_ids:
            plan = self._plan_repository.get_by_id(plan_id)

            if plan:
                monthly_cost = plan.pricing.calculate_monthly_cost(user_count)
                yearly_cost = plan.pricing.calculate_yearly_cost(user_count)
                setup_cost = plan.pricing.calculate_setup_cost()

                comparison[str(plan_id)] = {
                    "plan_name": plan.name.value,
                    "plan_type": plan.plan_type.value,
                    "monthly_cost": float(monthly_cost),
                    "yearly_cost": float(yearly_cost),
                    "setup_cost": float(setup_cost),
                    "yearly_savings": float(monthly_cost * 12 - yearly_cost),
                    "cost_per_user": float(plan.pricing.per_user_amount or 0),
                    "pricing_description": plan.pricing.get_pricing_description(),
                    "features": plan.features,
                    "limits": plan.limits,
                }

        return comparison

    def get_plan_feature_matrix(self) -> Dict[str, Dict[str, Any]]:
        """Get feature comparison matrix for all public plans."""
        public_plans = self._plan_repository.get_public_plans()
        features = self._feature_repository.get_active_features()

        matrix = {}

        for plan in public_plans:
            plan_features = {}

            for feature in features:
                feature_value = plan.get_feature_config(feature.name)
                plan_features[feature.name] = {
                    "enabled": bool(feature_value),
                    "config": feature_value,
                    "display_name": feature.display_name,
                    "description": feature.description,
                }

            matrix[plan.name.value] = {
                "plan_id": str(plan.id),
                "plan_type": plan.plan_type.value,
                "pricing": plan.pricing.get_pricing_description(),
                "max_users": plan.max_users,
                "features": plan_features,
                "limits": plan.limits,
            }

        return matrix

    def recommend_plan_for_organization(
        self,
        user_count: int,
        required_features: List[str],
        budget_monthly: Optional[Decimal] = None,
    ) -> List[Dict[str, Any]]:
        """Recommend plans based on requirements."""
        public_plans = self._plan_repository.get_public_plans()
        recommendations = []

        for plan in public_plans:
            # Check user capacity
            if not plan.can_support_users(user_count):
                continue

            # Check required features
            missing_features = []
            for feature in required_features:
                if not plan.is_feature_enabled(feature):
                    missing_features.append(feature)

            # Calculate cost
            monthly_cost = plan.pricing.calculate_monthly_cost(user_count)

            # Check budget constraint
            within_budget = budget_monthly is None or monthly_cost <= budget_monthly

            score = 0
            # Higher score for plans that meet all requirements
            if not missing_features:
                score += 50

            # Higher score for plans within budget
            if within_budget:
                score += 30

            # Lower score for more expensive plans (prefer cheaper when possible)
            if budget_monthly and monthly_cost <= budget_monthly * Decimal("0.8"):
                score += 20

            recommendations.append(
                {
                    "plan_id": str(plan.id),
                    "plan_name": plan.name.value,
                    "plan_type": plan.plan_type.value,
                    "monthly_cost": float(monthly_cost),
                    "missing_features": missing_features,
                    "within_budget": within_budget,
                    "score": score,
                    "reason": self._get_recommendation_reason(
                        plan, missing_features, within_budget
                    ),
                }
            )

        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        return recommendations[:3]  # Return top 3 recommendations

    def _get_recommendation_reason(
        self, plan: Plan, missing_features: List[str], within_budget: bool
    ) -> str:
        """Generate recommendation reason text."""
        if not missing_features and within_budget:
            return f"Perfect match! {plan.name.value} includes all required features within budget."

        if not missing_features:
            return f"{plan.name.value} includes all required features but may be over budget."

        if within_budget:
            feature_text = "features" if len(missing_features) > 1 else "feature"
            return f"{plan.name.value} is within budget but missing {len(missing_features)} {feature_text}."

        return f"{plan.name.value} is missing features and over budget."
