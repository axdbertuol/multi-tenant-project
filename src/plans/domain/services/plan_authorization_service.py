from typing import Dict, Any, List, Optional
from uuid import UUID

from ..entities.plan import Plan, PlanStatus, PlanType
from ..entities.organization_plan import OrganizationPlan
from ..repositories.plan_repository import PlanRepository
from ..repositories.organization_plan_repository import OrganizationPlanRepository


class PlanAuthorizationService:
    """Domain service for handling plan access authorization and visibility logic."""

    def __init__(
        self,
        plan_repository: PlanRepository,
        org_plan_repository: OrganizationPlanRepository,
    ):
        self._plan_repository = plan_repository
        self._org_plan_repository = org_plan_repository

    def authorize_plan_access(
        self,
        user_id: UUID,
        organization_id: UUID,
        plan_id: UUID,
        action: str = "view",
    ) -> tuple[bool, str]:
        """Authorize user access to a specific plan."""
        
        # Check if plan exists and is accessible
        plan = self._plan_repository.find_by_id(plan_id)
        if not plan:
            return False, "Plan not found"

        # Check plan visibility
        if not self._is_plan_visible_to_organization(plan, organization_id):
            return False, "Plan is not accessible"

        # For view access, check if plan is public or organization has subscription
        if action == "view":
            if plan.is_public:
                return True, "Public plan access granted"
            
            # Check if organization has access through subscription
            subscription = self._org_plan_repository.get_by_organization_id(organization_id)
            if subscription and subscription.plan_id == plan_id:
                return True, "Subscription-based access granted"
            
            return False, "No access to private plan"

        # For subscription actions, check plan availability
        if action in ["subscribe", "upgrade"]:
            if not plan.is_available_for_signup():
                return False, "Plan is not available for subscription"
            
            return True, "Subscription access authorized"

        # For administrative actions, perform additional checks
        if action in ["modify", "delete", "manage"]:
            # Only allow if user has administrative privileges (business logic)
            # This would typically integrate with IAM/user permissions
            return True, "Administrative access granted"  # Simplified for now

        return False, f"Unknown action: {action}"

    def get_authorized_plans_for_organization(
        self, organization_id: UUID, include_private: bool = False
    ) -> List[Plan]:
        """Get list of plans that an organization can access."""
        
        # Get all active public plans
        authorized_plans = []
        
        if include_private:
            # Get all active plans
            all_plans = self._plan_repository.find_active_plans()
        else:
            # Get only public plans
            all_plans = self._plan_repository.find_paginated(is_active=True)[0]
        
        for plan in all_plans:
            if self._is_plan_visible_to_organization(plan, organization_id):
                authorized_plans.append(plan)
        
        return authorized_plans

    def validate_plan_upgrade_path(
        self, 
        organization_id: UUID, 
        from_plan_id: UUID, 
        to_plan_id: UUID
    ) -> tuple[bool, str, Dict[str, Any]]:
        """Validate if organization can upgrade from one plan to another."""
        
        from_plan = self._plan_repository.find_by_id(from_plan_id)
        to_plan = self._plan_repository.find_by_id(to_plan_id)
        
        if not from_plan:
            return False, "Current plan not found", {}
        
        if not to_plan:
            return False, "Target plan not found", {}
        
        # Check if organization currently has the from_plan
        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription or subscription.plan_id != from_plan_id:
            return False, "Organization does not have the specified current plan", {}
        
        # Check if target plan is available
        if not to_plan.is_available_for_signup():
            return False, "Target plan is not available for subscription", {}
        
        # Validate upgrade path logic
        upgrade_info = self._analyze_upgrade_path(from_plan, to_plan)
        
        if not upgrade_info["is_valid_upgrade"]:
            return False, upgrade_info["reason"], upgrade_info
        
        return True, "Upgrade path is valid", upgrade_info

    def check_plan_visibility(
        self, plan_id: UUID, organization_id: Optional[UUID] = None
    ) -> tuple[bool, str]:
        """Check if a plan is visible to a specific organization or publicly."""
        
        plan = self._plan_repository.find_by_id(plan_id)
        if not plan:
            return False, "Plan not found"
        
        # Check basic visibility rules
        if not plan.is_active:
            return False, "Plan is inactive"
        
        if plan.status != PlanStatus.ACTIVE:
            return False, f"Plan status is {plan.status.value}"
        
        # Public plans are visible to everyone
        if plan.is_public:
            return True, "Plan is publicly visible"
        
        # Private plans require organization context
        if organization_id is None:
            return False, "Private plan requires organization context"
        
        # Check if organization has special access to private plan
        if self._has_private_plan_access(organization_id, plan_id):
            return True, "Organization has private plan access"
        
        return False, "Plan is private and not accessible"

    def validate_plan_subscription_limits(
        self, organization_id: UUID, plan_id: UUID
    ) -> tuple[bool, str, Dict[str, Any]]:
        """Validate if organization can subscribe to plan based on limits."""
        
        plan = self._plan_repository.find_by_id(plan_id)
        if not plan:
            return False, "Plan not found", {}
        
        # Check subscription limits (simplified business logic)
        validation_result = {
            "can_subscribe": True,
            "limit_checks": {},
            "warnings": [],
        }
        
        # Check if organization already has active subscription
        existing_subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if existing_subscription and existing_subscription.is_active():
            validation_result["can_subscribe"] = False
            return (
                False,
                "Organization already has an active subscription",
                validation_result,
            )
        
        # Additional business logic for subscription limits would go here
        # For example: checking organization size, usage history, etc.
        
        return True, "Subscription is allowed", validation_result

    def get_plan_access_summary(
        self, organization_id: UUID
    ) -> Dict[str, Any]:
        """Get comprehensive plan access summary for organization."""
        
        current_subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        available_plans = self.get_authorized_plans_for_organization(organization_id)
        
        summary = {
            "organization_id": str(organization_id),
            "current_subscription": None,
            "available_plans": [],
            "upgrade_options": [],
            "access_level": "public",
        }
        
        if current_subscription:
            current_plan = self._plan_repository.find_by_id(current_subscription.plan_id)
            if current_plan:
                summary["current_subscription"] = {
                    "plan_id": str(current_plan.id),
                    "plan_name": current_plan.name.value,
                    "plan_type": current_plan.plan_type.value,
                    "status": current_subscription.status.value,
                    "is_active": current_subscription.is_active(),
                }
                summary["access_level"] = "subscriber"
        
        # Process available plans
        for plan in available_plans:
            plan_info = {
                "id": str(plan.id),
                "name": plan.name.value,
                "type": plan.plan_type.value,
                "is_public": plan.is_public,
                "can_subscribe": plan.is_available_for_signup(),
            }
            
            # Check if this is an upgrade option
            if current_subscription:
                can_upgrade, _, upgrade_info = self.validate_plan_upgrade_path(
                    organization_id, current_subscription.plan_id, plan.id
                )
                if can_upgrade:
                    plan_info["is_upgrade_option"] = True
                    plan_info["upgrade_benefits"] = upgrade_info.get("benefits", [])
                    summary["upgrade_options"].append(plan_info)
            
            summary["available_plans"].append(plan_info)
        
        return summary

    def _is_plan_visible_to_organization(self, plan: Plan, organization_id: UUID) -> bool:
        """Check if plan is visible to organization."""
        # Public active plans are visible to everyone
        if plan.is_public and plan.is_active and plan.status == PlanStatus.ACTIVE:
            return True
        
        # Private plans require special access
        if not plan.is_public:
            return self._has_private_plan_access(organization_id, plan.id)
        
        return False

    def _has_private_plan_access(self, organization_id: UUID, plan_id: UUID) -> bool:
        """Check if organization has access to private plan."""
        # Check if organization currently subscribes to this plan
        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if subscription and subscription.plan_id == plan_id:
            return True
        
        # Additional business logic for private plan access would go here
        # For example: enterprise agreements, special partnerships, etc.
        
        return False

    def _analyze_upgrade_path(self, from_plan: Plan, to_plan: Plan) -> Dict[str, Any]:
        """Analyze upgrade path between two plans."""
        upgrade_info = {
            "is_valid_upgrade": True,
            "reason": "Valid upgrade path",
            "upgrade_type": "standard",
            "benefits": [],
            "considerations": [],
        }
        
        # Basic upgrade validation
        if from_plan.id == to_plan.id:
            upgrade_info["is_valid_upgrade"] = False
            upgrade_info["reason"] = "Cannot upgrade to the same plan"
            return upgrade_info
        
        # Plan type progression logic
        plan_type_hierarchy = {
            PlanType.BASIC: 1,
            PlanType.PREMIUM: 2,
            PlanType.ENTERPRISE: 3,
        }
        
        from_level = plan_type_hierarchy.get(from_plan.plan_type, 0)
        to_level = plan_type_hierarchy.get(to_plan.plan_type, 0)
        
        if to_level < from_level:
            upgrade_info["upgrade_type"] = "downgrade"
            upgrade_info["considerations"].append("This is a downgrade - some features may be lost")
        elif to_level > from_level:
            upgrade_info["upgrade_type"] = "upgrade"
            upgrade_info["benefits"].append("Access to more features and higher limits")
        else:
            upgrade_info["upgrade_type"] = "lateral"
            upgrade_info["considerations"].append("Similar feature level - check specific differences")
        
        # Add pricing considerations
        if to_plan.pricing.monthly_price > from_plan.pricing.monthly_price:
            upgrade_info["considerations"].append("Higher monthly cost")
        elif to_plan.pricing.monthly_price < from_plan.pricing.monthly_price:
            upgrade_info["benefits"].append("Lower monthly cost")
        
        return upgrade_info