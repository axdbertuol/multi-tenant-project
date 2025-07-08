from typing import Dict, Any, Optional
from uuid import UUID

from ...application.use_cases.onboard_tenant import PlansService
from ....plans.application.use_cases.plan_use_cases import PlanUseCase
from ....plans.domain.entities.organization_plan import OrganizationPlan, BillingCycle
from ....plans.domain.repositories.organization_plan_repository import OrganizationPlanRepository
from ....plans.domain.repositories.plan_repository import PlanRepository
from ....shared.domain.repositories.unit_of_work import UnitOfWork


class PlansServiceImpl(PlansService):
    def __init__(
        self,
        plan_use_case: PlanUseCase,
        uow: UnitOfWork,
    ):
        self.plan_use_case = plan_use_case
        self.uow = uow
        self._plan_repository: PlanRepository = uow.get_repository("plan")
        self._organization_plan_repository: OrganizationPlanRepository = uow.get_repository("organization_plan")

    def create_application_instance(self, tenant_id: str, plan_id: str) -> str:
        """Create application instance for tenant with specified plan."""
        with self.uow:
            # Get plan to validate it exists
            plan = self._plan_repository.find_by_id(UUID(plan_id))
            if not plan:
                raise ValueError(f"Plan {plan_id} not found")
            
            # Check if organization already has a plan
            existing_plan = self._organization_plan_repository.get_by_organization_id(
                UUID(tenant_id)
            )
            if existing_plan:
                raise ValueError(f"Organization {tenant_id} already has a plan subscription")
            
            # Create organization plan subscription with trial period
            organization_plan = OrganizationPlan.create(
                organization_id=UUID(tenant_id),
                plan_id=UUID(plan_id),
                billing_cycle=BillingCycle.MONTHLY,
                trial_days=14,  # 14-day trial for new tenants
            )
            
            # Save the subscription
            saved_plan = self._organization_plan_repository.save(organization_plan)
            
            return str(saved_plan.id)

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get plan details."""
        plan_response = self.plan_use_case.get_plan_by_id(UUID(plan_id))
        if not plan_response:
            return None
        
        return {
            "id": str(plan_response.id),
            "name": plan_response.name,
            "description": plan_response.description,
            "plan_type": plan_response.plan_type,
            "resources": plan_response.resources,
            "price_monthly": plan_response.price_monthly,
            "price_yearly": plan_response.price_yearly,
            "is_active": plan_response.is_active,
            "created_at": plan_response.created_at.isoformat(),
            "updated_at": plan_response.updated_at.isoformat() if plan_response.updated_at else None,
        }

    def get_trial_plan_id(self) -> str:
        """Get the default trial plan ID (usually basic plan)."""
        active_plans = self.plan_use_case.get_active_plans()
        
        # Look for basic plan first
        for plan in active_plans:
            if plan.plan_type.lower() == "basic":
                return str(plan.id)
        
        # If no basic plan, return first active plan
        if active_plans:
            return str(active_plans[0].id)
        
        raise ValueError("No active plans available for trial")

    def get_plan_resources(self, plan_id: str) -> Dict[str, Any]:
        """Get plan resources configuration."""
        plan_features = self.plan_use_case.get_plan_features(UUID(plan_id))
        if not plan_features:
            return {}
        
        return plan_features.get("resources", {})

    def validate_plan_access(self, tenant_id: str, resource_type: str, action: str) -> bool:
        """Validate if tenant can access specific resource/action."""
        try:
            # Get organization's current plan
            organization_plan = self._organization_plan_repository.get_by_organization_id(
                UUID(tenant_id)
            )
            if not organization_plan:
                return False
            
            # Get plan details
            plan = self._plan_repository.find_by_id(organization_plan.plan_id)
            if not plan:
                return False
            
            # Check if resource is enabled in plan
            resource_config = plan.resources.get(resource_type, {})
            if not resource_config.get("enabled", False):
                return False
            
            # For now, if resource is enabled, allow all actions
            # In the future, this could be more granular
            return True
            
        except Exception:
            return False