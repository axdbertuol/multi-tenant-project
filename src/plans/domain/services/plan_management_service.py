from typing import Dict, Any, List, Optional
from uuid import UUID

from ..entities.plan import Plan, PlanType, PlanStatus
from ..value_objects.plan_name import PlanName
from ..value_objects.pricing import Pricing
from ..repositories.plan_repository import PlanRepository
from ..repositories.organization_plan_repository import OrganizationPlanRepository


class PlanManagementService:
    """Domain service for managing plan lifecycle and business rules."""

    def __init__(
        self,
        plan_repository: PlanRepository,
        org_plan_repository: OrganizationPlanRepository,
    ):
        self._plan_repository = plan_repository
        self._org_plan_repository = org_plan_repository

    def create_plan(
        self,
        name: str,
        description: str,
        plan_type: PlanType,
        pricing: Pricing,
        max_users: int = 10,
        max_organizations: int = 1,
        resources: Optional[Dict[str, Any]] = None,
        is_public: bool = True,
    ) -> Plan:
        """Create a new plan with validation."""
        
        # Validate plan name uniqueness
        existing_plan = self._plan_repository.find_by_name(PlanName(name))
        if existing_plan:
            raise ValueError(f"Plan with name '{name}' already exists")
        
        # Validate business rules
        self._validate_plan_creation_rules(
            name, plan_type, pricing, max_users, max_organizations
        )
        
        # Create plan
        plan = Plan.create(
            name=name,
            description=description,
            plan_type=plan_type,
            pricing=pricing,
            max_users=max_users,
            max_organizations=max_organizations,
            resources=resources,
            is_public=is_public,
        )
        
        return self._plan_repository.save(plan)

    def update_plan(
        self,
        plan_id: UUID,
        updates: Dict[str, Any],
    ) -> Plan:
        """Update an existing plan with validation."""
        
        plan = self._plan_repository.find_by_id(plan_id)
        if not plan:
            raise ValueError("Plan not found")
        
        # Check if plan can be modified
        if not self._can_modify_plan(plan):
            raise ValueError("Plan cannot be modified due to active subscriptions")
        
        # Apply updates with validation
        updated_plan = plan
        
        if "description" in updates:
            updated_plan = updated_plan.update_description(updates["description"])
        
        if "pricing" in updates:
            new_pricing = updates["pricing"]
            if isinstance(new_pricing, dict):
                new_pricing = Pricing(**new_pricing)
            self._validate_pricing_update(plan, new_pricing)
            updated_plan = updated_plan.update_pricing(new_pricing)
        
        if "resources" in updates:
            for resource_type, config in updates["resources"].items():
                updated_plan = updated_plan.update_resource(resource_type, config)
        
        return self._plan_repository.save(updated_plan)

    def archive_plan(self, plan_id: UUID, force: bool = False) -> Plan:
        """Archive a plan (soft delete)."""
        
        plan = self._plan_repository.find_by_id(plan_id)
        if not plan:
            raise ValueError("Plan not found")
        
        # Check for active subscriptions
        active_subscriptions = self._org_plan_repository.count_active_subscriptions(plan_id)
        
        if active_subscriptions > 0 and not force:
            raise ValueError(
                f"Cannot archive plan with {active_subscriptions} active subscriptions. "
                "Use force=True to archive anyway."
            )
        
        # Archive the plan
        archived_plan = plan.deprecate()
        return self._plan_repository.save(archived_plan)

    def validate_plan_rules(self, plan: Plan) -> tuple[bool, List[str]]:
        """Validate plan against business rules."""
        
        issues = []
        
        # Validate pricing
        if plan.pricing.monthly_price <= 0 and plan.plan_type != PlanType.BASIC:
            issues.append("Non-basic plans must have positive monthly pricing")
        
        # Validate user limits
        if plan.max_users <= 0:
            issues.append("Maximum users must be positive")
        
        # Validate organization limits
        if plan.max_organizations <= 0:
            issues.append("Maximum organizations must be positive")
        
        # Validate resource configuration
        resource_issues = self._validate_plan_resources(plan)
        issues.extend(resource_issues)
        
        # Plan type specific validations
        type_issues = self._validate_plan_type_rules(plan)
        issues.extend(type_issues)
        
        return len(issues) == 0, issues

    def duplicate_plan(
        self,
        source_plan_id: UUID,
        new_name: str,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> Plan:
        """Create a new plan based on an existing plan."""
        
        source_plan = self._plan_repository.find_by_id(source_plan_id)
        if not source_plan:
            raise ValueError("Source plan not found")
        
        # Check name uniqueness
        existing_plan = self._plan_repository.find_by_name(PlanName(new_name))
        if existing_plan:
            raise ValueError(f"Plan with name '{new_name}' already exists")
        
        # Create new plan with copied properties
        new_plan_data = {
            "name": new_name,
            "description": modifications.get("description", f"Copy of {source_plan.description}"),
            "plan_type": modifications.get("plan_type", source_plan.plan_type),
            "pricing": modifications.get("pricing", source_plan.pricing),
            "max_users": modifications.get("max_users", source_plan.max_users),
            "max_organizations": modifications.get("max_organizations", source_plan.max_organizations),
            "resources": modifications.get("resources", source_plan.resources.copy()),
            "is_public": modifications.get("is_public", source_plan.is_public),
        }
        
        return self.create_plan(**new_plan_data)

    def get_plan_usage_statistics(self, plan_id: UUID) -> Dict[str, Any]:
        """Get usage statistics for a plan."""
        
        plan = self._plan_repository.find_by_id(plan_id)
        if not plan:
            raise ValueError("Plan not found")
        
        # Get subscription statistics
        active_subscriptions = self._org_plan_repository.count_active_subscriptions(plan_id)
        all_subscriptions = self._org_plan_repository.get_by_plan_id(plan_id)
        
        # Calculate statistics
        total_subscriptions = len(all_subscriptions)
        cancelled_subscriptions = len([s for s in all_subscriptions if s.is_cancelled()])
        expired_subscriptions = len([s for s in all_subscriptions if s.is_expired()])
        
        # Revenue calculation (simplified)
        monthly_revenue = active_subscriptions * plan.pricing.monthly_price
        yearly_revenue = sum(
            s.billing_cycle == "yearly" and s.is_active() 
            for s in all_subscriptions
        ) * plan.pricing.yearly_price if plan.pricing.yearly_price else 0
        
        return {
            "plan_id": str(plan_id),
            "plan_name": plan.name.value,
            "subscriptions": {
                "active": active_subscriptions,
                "total": total_subscriptions,
                "cancelled": cancelled_subscriptions,
                "expired": expired_subscriptions,
                "retention_rate": (active_subscriptions / max(total_subscriptions, 1)) * 100,
            },
            "revenue": {
                "monthly_mrr": monthly_revenue,
                "yearly_arr": yearly_revenue,
                "total_potential": monthly_revenue * 12 + yearly_revenue,
            },
            "plan_health": self._assess_plan_health(active_subscriptions, total_subscriptions),
        }

    def recommend_plan_optimizations(self, plan_id: UUID) -> List[Dict[str, Any]]:
        """Recommend optimizations for a plan."""
        
        plan = self._plan_repository.find_by_id(plan_id)
        if not plan:
            raise ValueError("Plan not found")
        
        recommendations = []
        
        # Get usage statistics
        stats = self.get_plan_usage_statistics(plan_id)
        
        # Low adoption rate
        if stats["subscriptions"]["active"] < 5:
            recommendations.append({
                "type": "low_adoption",
                "priority": "medium",
                "title": "Low Plan Adoption",
                "description": "Consider reviewing pricing or features to increase appeal",
                "actions": ["Review pricing strategy", "Analyze competitor offerings", "Survey potential customers"]
            })
        
        # High churn rate
        retention_rate = stats["subscriptions"]["retention_rate"]
        if retention_rate < 70:
            recommendations.append({
                "type": "high_churn",
                "priority": "high",
                "title": "High Churn Rate",
                "description": f"Retention rate of {retention_rate:.1f}% is below optimal",
                "actions": ["Analyze cancellation reasons", "Improve onboarding", "Add retention features"]
            })
        
        # Pricing optimization
        if plan.pricing.yearly_price and plan.pricing.yearly_price < plan.pricing.monthly_price * 10:
            recommendations.append({
                "type": "pricing_optimization",
                "priority": "low",
                "title": "Yearly Pricing Incentive",
                "description": "Consider offering better yearly pricing discount",
                "actions": ["Increase yearly discount", "Promote annual billing"]
            })
        
        # Resource utilization
        resource_recommendations = self._analyze_resource_usage(plan)
        recommendations.extend(resource_recommendations)
        
        return recommendations

    def _validate_plan_creation_rules(
        self,
        name: str,
        plan_type: PlanType,
        pricing: Pricing,
        max_users: int,
        max_organizations: int,
    ) -> None:
        """Validate plan creation business rules."""
        
        if len(name) < 3 or len(name) > 50:
            raise ValueError("Plan name must be between 3 and 50 characters")
        
        if max_users <= 0:
            raise ValueError("Maximum users must be positive")
        
        if max_organizations <= 0:
            raise ValueError("Maximum organizations must be positive")
        
        # Plan type specific rules
        if plan_type == PlanType.BASIC and pricing.monthly_price > 50:
            raise ValueError("Basic plans should not exceed $50/month")
        
        if plan_type == PlanType.ENTERPRISE and pricing.monthly_price < 100:
            raise ValueError("Enterprise plans should be at least $100/month")

    def _can_modify_plan(self, plan: Plan) -> bool:
        """Check if plan can be safely modified."""
        
        # Check for active subscriptions
        active_count = self._org_plan_repository.count_active_subscriptions(plan.id)
        
        # Plans with active subscriptions require careful modification
        if active_count > 0:
            # Only allow certain modifications
            return plan.status == PlanStatus.ACTIVE
        
        return True

    def _validate_pricing_update(self, current_plan: Plan, new_pricing: Pricing) -> None:
        """Validate pricing updates."""
        
        # Check for significant price increases
        if new_pricing.monthly_price > current_plan.pricing.monthly_price * 1.5:
            active_subs = self._org_plan_repository.count_active_subscriptions(current_plan.id)
            if active_subs > 0:
                raise ValueError(
                    "Cannot increase price by more than 50% for plans with active subscriptions"
                )

    def _validate_plan_resources(self, plan: Plan) -> List[str]:
        """Validate plan resource configuration."""
        
        issues = []
        
        for resource_type, config in plan.resources.items():
            if not isinstance(config, dict):
                issues.append(f"Resource {resource_type} configuration must be a dictionary")
                continue
            
            # Validate required resource fields
            if "enabled" not in config:
                issues.append(f"Resource {resource_type} must have 'enabled' field")
            
            # Validate resource-specific rules
            if resource_type == "whatsapp_app" and config.get("enabled"):
                if not config.get("api_keys", {}).get("whatsapp_api_key"):
                    issues.append("WhatsApp resource requires API key configuration")
            
            if resource_type == "web_chat_app" and config.get("enabled"):
                limits = config.get("limits", {})
                if limits.get("concurrent_sessions", 0) <= 0:
                    issues.append("Web chat app requires positive concurrent session limit")
        
        return issues

    def _validate_plan_type_rules(self, plan: Plan) -> List[str]:
        """Validate plan type specific business rules."""
        
        issues = []
        
        if plan.plan_type == PlanType.BASIC:
            # Basic plans should have limited features
            if plan.max_users > 25:
                issues.append("Basic plans should not exceed 25 users")
            
            if plan.has_resource("whatsapp_app"):
                issues.append("Basic plans should not include WhatsApp integration")
        
        elif plan.plan_type == PlanType.ENTERPRISE:
            # Enterprise plans should have comprehensive features
            if not plan.has_resource("api_access"):
                issues.append("Enterprise plans should include API access")
            
            if plan.max_organizations < 5:
                issues.append("Enterprise plans should support at least 5 organizations")
        
        return issues

    def _assess_plan_health(self, active_subs: int, total_subs: int) -> str:
        """Assess the overall health of a plan."""
        
        if total_subs == 0:
            return "new"
        
        retention_rate = (active_subs / total_subs) * 100
        
        if retention_rate >= 80:
            return "healthy"
        elif retention_rate >= 60:
            return "moderate"
        else:
            return "needs_attention"

    def _analyze_resource_usage(self, plan: Plan) -> List[Dict[str, Any]]:
        """Analyze resource usage and recommend optimizations."""
        
        recommendations = []
        
        # Check for unused resources
        enabled_resources = [
            resource_type for resource_type, config in plan.resources.items()
            if config.get("enabled", False)
        ]
        
        if len(enabled_resources) > 5:
            recommendations.append({
                "type": "resource_complexity",
                "priority": "low",
                "title": "High Resource Complexity",
                "description": "Plan has many enabled resources which may confuse users",
                "actions": ["Consider creating simpler plan variants", "Group related resources"]
            })
        
        # Check for missing common resources
        if not plan.has_resource("management_app"):
            recommendations.append({
                "type": "missing_core_resource",
                "priority": "medium",
                "title": "Missing Management App",
                "description": "Plans should typically include management capabilities",
                "actions": ["Enable management app resource", "Review resource strategy"]
            })
        
        return recommendations