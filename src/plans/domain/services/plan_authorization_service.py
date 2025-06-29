from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from ..entities.plan import Plan
from ..entities.plan_resource import PlanResource, PlanResourceType
from ..entities.plan_configuration import PlanConfiguration
from ..repositories.plan_repository import PlanRepository
from ..repositories.plan_resource_repository import PlanResourceRepository
from ..repositories.plan_configuration_repository import PlanConfigurationRepository
from ..repositories.organization_plan_repository import OrganizationPlanRepository


class PlanAuthorizationService:
    """Domain service for integrating plans with authorization system."""

    def __init__(
        self,
        plan_repository: PlanRepository,
        resource_repository: PlanResourceRepository,
        configuration_repository: PlanConfigurationRepository,
        org_plan_repository: OrganizationPlanRepository,
    ):
        self._plan_repository = plan_repository
        self._resource_repository = resource_repository
        self._configuration_repository = configuration_repository
        self._org_plan_repository = org_plan_repository

    def validate_organization_resource_access(
        self, organization_id: UUID, resource_type: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate if organization has access to a specific resource type."""

        # Get organization's current plan
        org_plan = self._org_plan_repository.get_by_organization_id(organization_id)
        if not org_plan or not org_plan.is_active():
            return False, "Organization has no active plan", None

        # Get plan details
        plan = self._plan_repository.get_by_id(org_plan.plan_id)
        if not plan or not plan.is_active:
            return False, "Plan is not active", None

        # Check if plan has the resource
        if not plan.has_resource(resource_type):
            return (
                False,
                f"Resource '{resource_type}' not available in current plan",
                None,
            )

        # Get resource configuration
        resource_config = plan.get_resource_config(resource_type)

        # Validate resource configuration
        is_valid, errors = plan.validate_resource_requirements(resource_type)
        if not is_valid:
            return False, f"Resource configuration invalid: {', '.join(errors)}", None

        # Apply organization-specific overrides
        effective_config = self._apply_organization_overrides(resource_config, org_plan)

        return True, "Access granted", effective_config

    def validate_api_key_requirements(
        self, organization_id: UUID, resource_type: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Validate API key requirements for resource access."""

        has_access, message, config = self.validate_organization_resource_access(
            organization_id, resource_type
        )

        if not has_access:
            return False, message, None

        # Determine required API key based on resource type
        required_key = None
        if resource_type == "chat_whatsapp":
            required_key = "whatsapp_api_key"
        elif resource_type == "chat_iframe":
            required_key = "iframe_api_key"

        if not required_key:
            return True, "No API key required", None

        # Check if API key is configured
        api_keys = config.get("api_keys", {}) if config else {}
        api_key_value = api_keys.get(required_key)

        if not api_key_value:
            return False, f"Required API key '{required_key}' not configured", None

        return True, "API key validation passed", api_key_value

    def get_organization_resource_limits(
        self, organization_id: UUID, resource_type: str
    ) -> Optional[Dict[str, int]]:
        """Get effective resource limits for organization."""

        has_access, _, config = self.validate_organization_resource_access(
            organization_id, resource_type
        )

        if not has_access or not config:
            return None

        return config.get("limits", {})

    def get_organization_enabled_features(
        self, organization_id: UUID, resource_type: str
    ) -> List[str]:
        """Get enabled features for organization's resource."""

        has_access, _, config = self.validate_organization_resource_access(
            organization_id, resource_type
        )

        if not has_access or not config:
            return []

        return config.get("enabled_features", [])

    def can_organization_use_feature(
        self, organization_id: UUID, resource_type: str, feature_name: str
    ) -> bool:
        """Check if organization can use a specific feature."""

        enabled_features = self.get_organization_enabled_features(
            organization_id, resource_type
        )

        return feature_name in enabled_features

    def validate_resource_usage_limits(
        self,
        organization_id: UUID,
        resource_type: str,
        usage_type: str,
        requested_amount: int = 1,
    ) -> Tuple[bool, str, Optional[int]]:
        """Validate if organization can use resource within limits."""

        limits = self.get_organization_resource_limits(organization_id, resource_type)

        if not limits:
            return False, "No resource limits found", None

        limit_value = limits.get(usage_type)

        if limit_value is None:
            return True, "No limit set for usage type", None

        if limit_value == -1:  # Unlimited
            return True, "Unlimited usage allowed", -1

        # Here you would typically check current usage against the limit
        # For now, we'll assume the requested amount is within limits
        if requested_amount <= limit_value:
            return True, "Within usage limits", limit_value - requested_amount

        return False, f"Would exceed limit of {limit_value}", limit_value

    def get_organization_plan_summary(
        self, organization_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get comprehensive plan summary for organization."""

        org_plan = self._org_plan_repository.get_by_organization_id(organization_id)
        if not org_plan:
            return None

        plan = self._plan_repository.get_by_id(org_plan.plan_id)
        if not plan:
            return None

        # Get all resources for the plan
        resources_summary = {}
        for resource_type in plan.resources.keys():
            has_access, message, config = self.validate_organization_resource_access(
                organization_id, resource_type
            )

            resources_summary[resource_type] = {
                "has_access": has_access,
                "message": message,
                "configuration": config,
                "enabled_features": config.get("enabled_features", [])
                if config
                else [],
                "limits": config.get("limits", {}) if config else {},
            }

        return {
            "organization_id": str(organization_id),
            "plan": {
                "id": str(plan.id),
                "name": plan.name.value,
                "type": plan.plan_type.value,
                "is_active": plan.is_active,
            },
            "subscription": {
                "id": str(org_plan.id),
                "status": org_plan.status.value,
                "is_active": org_plan.is_active(),
                "expires_at": org_plan.expires_at.isoformat()
                if org_plan.expires_at
                else None,
            },
            "resources": resources_summary,
        }

    def _apply_organization_overrides(
        self, base_config: Dict[str, Any], org_plan
    ) -> Dict[str, Any]:
        """Apply organization-specific configuration overrides."""

        effective_config = base_config.copy()

        # Apply feature overrides from organization plan
        if org_plan.feature_overrides:
            for key, value in org_plan.feature_overrides.items():
                if key in effective_config:
                    if isinstance(value, dict) and isinstance(
                        effective_config[key], dict
                    ):
                        effective_config[key].update(value)
                    else:
                        effective_config[key] = value

        # Apply limit overrides from organization plan
        if org_plan.limit_overrides:
            if "limits" not in effective_config:
                effective_config["limits"] = {}
            effective_config["limits"].update(org_plan.limit_overrides)

        return effective_config

    def create_plan_with_resources(
        self, plan_name: str, plan_type: str, resources_config: List[Dict[str, Any]]
    ) -> Plan:
        """Create a new plan with associated resources."""
        from ..entities.plan import PlanType
        from ..value_objects.pricing import Pricing, Currency
        from decimal import Decimal

        # Create plan
        plan = Plan.create(
            name=plan_name,
            description=f"{plan_type.title()} plan with resources",
            plan_type=PlanType(plan_type),
            pricing=Pricing.create_fixed(Decimal("99.00"), Currency.USD),
            resources={},
        )

        saved_plan = self._plan_repository.save(plan)

        # Create resources
        for resource_config in resources_config:
            resource_type = PlanResourceType(resource_config["resource_type"])
            configuration = resource_config["configuration"]

            resource = PlanResource.create(
                plan_id=saved_plan.id,
                resource_type=resource_type,
                configuration=configuration,
            )

            self._resource_repository.save(resource)

        # Create configuration
        api_keys = {}
        limits = {}
        enabled_features = []

        for resource_config in resources_config:
            config = resource_config["configuration"]
            if "api_keys" in config:
                api_keys.update(config["api_keys"])
            if "limits" in config:
                limits.update(config["limits"])
            if "enabled_features" in config:
                enabled_features.extend(config["enabled_features"])

        plan_configuration = PlanConfiguration.create(
            plan_id=saved_plan.id,
            api_keys=api_keys,
            limits=limits,
            enabled_features=list(set(enabled_features)),  # Remove duplicates
        )

        self._configuration_repository.save(plan_configuration)

        return saved_plan
