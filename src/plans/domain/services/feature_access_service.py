from typing import Dict, Any, Optional, List
from uuid import UUID

from ..entities.organization_plan import OrganizationPlan
from ..repositories.organization_plan_repository import OrganizationPlanRepository
from ..repositories.plan_repository import PlanRepository
from ..value_objects.chat_configuration import (
    ChatWhatsAppConfiguration,
    ChatIframeConfiguration,
)


class FeatureAccessService:
    """Domain service for managing feature access and configurations."""

    def __init__(
        self,
        org_plan_repository: OrganizationPlanRepository,
        plan_repository: PlanRepository,
    ):
        self._org_plan_repository = org_plan_repository
        self._plan_repository = plan_repository

    def has_feature_access(
        self, organization_id: UUID, feature_name: str
    ) -> tuple[bool, str]:
        """Check if organization has access to a specific feature."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription or not subscription.is_active():
            return False, "No active subscription"

        plan = self._plan_repository.get_by_id(subscription.plan_id)
        if not plan:
            return False, "Plan not found"

        # Check effective feature value (plan + overrides)
        effective_value = subscription.get_effective_feature_value(
            feature_name, plan.get_feature_config(feature_name)
        )

        if not effective_value:
            return False, f"Feature '{feature_name}' not available in current plan"

        return True, "Feature access granted"

    def get_chat_whatsapp_config(
        self, organization_id: UUID
    ) -> Optional[ChatWhatsAppConfiguration]:
        """Get WhatsApp chat configuration for organization."""

        has_access, _ = self.has_feature_access(organization_id, "chat_whatsapp")
        if not has_access:
            return None

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            return None

        # Get configuration from feature overrides or default
        config_data = subscription.feature_overrides.get("chat_whatsapp")

        if isinstance(config_data, dict):
            try:
                return ChatWhatsAppConfiguration(**config_data)
            except Exception:
                # Return default config if custom config is invalid
                return ChatWhatsAppConfiguration.create_default()

        return ChatWhatsAppConfiguration.create_default()

    def update_chat_whatsapp_config(
        self, organization_id: UUID, config: ChatWhatsAppConfiguration
    ) -> OrganizationPlan:
        """Update WhatsApp chat configuration for organization."""

        has_access, reason = self.has_feature_access(organization_id, "chat_whatsapp")
        if not has_access:
            raise ValueError(f"Cannot update WhatsApp config: {reason}")

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            raise ValueError("No active subscription found")

        # Validate configuration
        is_valid, issues = config.is_properly_configured()
        if not is_valid:
            raise ValueError(f"Invalid WhatsApp configuration: {', '.join(issues)}")

        # Update feature override
        updated_subscription = subscription.set_feature_override(
            "chat_whatsapp", config.model_dump()
        )

        return self._org_plan_repository.save(updated_subscription)

    def get_chat_iframe_config(
        self, organization_id: UUID
    ) -> Optional[ChatIframeConfiguration]:
        """Get iframe chat configuration for organization."""

        has_access, _ = self.has_feature_access(organization_id, "chat_iframe")
        if not has_access:
            return None

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            return None

        # Get configuration from feature overrides or default
        config_data = subscription.feature_overrides.get("chat_iframe")

        if isinstance(config_data, dict):
            try:
                return ChatIframeConfiguration(**config_data)
            except Exception:
                # Return default config if custom config is invalid
                return ChatIframeConfiguration.create_default()

        return ChatIframeConfiguration.create_default()

    def update_chat_iframe_config(
        self, organization_id: UUID, config: ChatIframeConfiguration
    ) -> OrganizationPlan:
        """Update iframe chat configuration for organization."""

        has_access, reason = self.has_feature_access(organization_id, "chat_iframe")
        if not has_access:
            raise ValueError(f"Cannot update iframe chat config: {reason}")

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            raise ValueError("No active subscription found")

        # Update feature override
        updated_subscription = subscription.set_feature_override(
            "chat_iframe", config.model_dump()
        )

        return self._org_plan_repository.save(updated_subscription)

    def get_feature_configurations(self, organization_id: UUID) -> Dict[str, Any]:
        """Get all feature configurations for organization."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription or not subscription.is_active():
            return {}

        plan = self._plan_repository.get_by_id(subscription.plan_id)
        if not plan:
            return {}

        configurations = {}

        # Chat WhatsApp
        if subscription.get_effective_feature_value(
            "chat_whatsapp", plan.get_feature_config("chat_whatsapp")
        ):
            whatsapp_config = self.get_chat_whatsapp_config(organization_id)
            if whatsapp_config:
                configurations["chat_whatsapp"] = whatsapp_config.model_dump()

        # Chat Iframe
        if subscription.get_effective_feature_value(
            "chat_iframe", plan.get_feature_config("chat_iframe")
        ):
            iframe_config = self.get_chat_iframe_config(organization_id)
            if iframe_config:
                configurations["chat_iframe"] = iframe_config.model_dump()

        return configurations

    def get_available_features(self, organization_id: UUID) -> List[Dict[str, Any]]:
        """Get list of available features for organization."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription or not subscription.is_active():
            return []

        plan = self._plan_repository.get_by_id(subscription.plan_id)
        if not plan:
            return []

        available_features = []

        # Process each feature
        for feature_name, plan_config in plan.features.items():
            effective_config = subscription.get_effective_feature_value(
                feature_name, plan_config
            )

            if effective_config:
                feature_info = {
                    "name": feature_name,
                    "enabled": bool(effective_config),
                    "config": effective_config,
                    "overridden": feature_name in subscription.feature_overrides,
                }

                # Add specific information for chat features
                if feature_name == "chat_whatsapp":
                    config = self.get_chat_whatsapp_config(organization_id)
                    feature_info["configuration_status"] = (
                        "configured" if config and config.enabled else "not_configured"
                    )

                elif feature_name == "chat_iframe":
                    config = self.get_chat_iframe_config(organization_id)
                    feature_info["configuration_status"] = (
                        "configured" if config and config.enabled else "not_configured"
                    )

                available_features.append(feature_info)

        return available_features

    def validate_feature_requirements(
        self, organization_id: UUID, required_features: List[str]
    ) -> Dict[str, Any]:
        """Validate if organization has access to all required features."""

        validation_result = {
            "all_requirements_met": True,
            "available_features": [],
            "missing_features": [],
            "upgrade_required": False,
        }

        for feature_name in required_features:
            has_access, reason = self.has_feature_access(organization_id, feature_name)

            if has_access:
                validation_result["available_features"].append(feature_name)
            else:
                validation_result["missing_features"].append(
                    {"feature": feature_name, "reason": reason}
                )
                validation_result["all_requirements_met"] = False
                validation_result["upgrade_required"] = True

        return validation_result

    def get_iframe_embed_code(
        self, organization_id: UUID, chat_endpoint: str
    ) -> Optional[str]:
        """Generate iframe embed code for organization."""

        config = self.get_chat_iframe_config(organization_id)
        if not config or not config.enabled:
            return None

        return config.get_embed_code(str(organization_id), chat_endpoint)

    def is_domain_allowed_for_iframe(self, organization_id: UUID, domain: str) -> bool:
        """Check if domain is allowed to embed iframe chat."""

        config = self.get_chat_iframe_config(organization_id)
        if not config or not config.enabled:
            return False

        return config.is_domain_allowed(domain)

    def enable_feature_for_organization(
        self, organization_id: UUID, feature_name: str, config: Optional[Any] = None
    ) -> OrganizationPlan:
        """Enable a feature for organization with custom configuration."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            raise ValueError("No active subscription found")

        plan = self._plan_repository.get_by_id(subscription.plan_id)
        if not plan:
            raise ValueError("Plan not found")

        # Check if feature exists in plan (even if disabled)
        if feature_name not in plan.features:
            raise ValueError(f"Feature '{feature_name}' not available in current plan")

        # Set feature override to enable it
        feature_config = config if config is not None else True
        updated_subscription = subscription.set_feature_override(
            feature_name, feature_config
        )

        return self._org_plan_repository.save(updated_subscription)

    def disable_feature_for_organization(
        self, organization_id: UUID, feature_name: str
    ) -> OrganizationPlan:
        """Disable a feature for organization."""

        subscription = self._org_plan_repository.get_by_organization_id(organization_id)
        if not subscription:
            raise ValueError("No active subscription found")

        # Set feature override to disable it
        updated_subscription = subscription.set_feature_override(feature_name, False)

        return self._org_plan_repository.save(updated_subscription)
