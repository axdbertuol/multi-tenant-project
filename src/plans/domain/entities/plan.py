from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum

from ..value_objects.plan_name import PlanName
from ..value_objects.pricing import Pricing


class PlanType(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class PlanStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class Plan(BaseModel):
    id: UUID
    name: PlanName
    description: str
    plan_type: PlanType
    pricing: Pricing
    max_users: int
    max_organizations: int
    resources: Dict[str, Any]  # Associated resources configuration
    is_active: bool = True
    status: PlanStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_public: bool = True

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        plan_type: PlanType,
        pricing: Pricing,
        max_users: int = 10,
        max_organizations: int = 1,
        resources: Optional[Dict[str, Any]] = None,
        is_public: bool = True,
    ) -> "Plan":
        return cls(
            id=uuid4(),
            name=PlanName(value=name),
            description=description,
            plan_type=plan_type,
            pricing=pricing,
            max_users=max_users,
            max_organizations=max_organizations,
            resources=resources or cls._get_default_resources(plan_type),
            is_active=True,
            status=PlanStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            is_public=is_public,
        )

    @staticmethod
    def _get_default_resources(plan_type: PlanType) -> Dict[str, Any]:
        """Get default resources configuration based on plan type."""
        if plan_type == PlanType.BASIC:
            return {
                "web_chat_app": {
                    "enabled": True,
                    "api_keys": {"iframe_api_key": "basic-iframe-key"},
                    "limits": {"concurrent_sessions": 25, "domains_allowed": 3},
                    "enabled_features": ["basic_chat", "emoji_support"],
                },
                "management_app": {
                    "enabled": True,
                    "limits": {"max_users": 10, "max_organizations": 1, "storage_gb": 5},
                    "enabled_features": ["dashboard", "user_management"],
                },
            }

        elif plan_type == PlanType.PREMIUM:
            return {
                "web_chat_app": {
                    "enabled": True,
                    "api_keys": {"iframe_api_key": "premium-iframe-key"},
                    "limits": {"concurrent_sessions": 100, "domains_allowed": 10},
                    "enabled_features": [
                        "basic_chat",
                        "emoji_support",
                        "custom_css",
                        "file_upload",
                    ],
                },
                "management_app": {
                    "enabled": True,
                    "limits": {"max_users": 25, "max_organizations": 3, "storage_gb": 25},
                    "enabled_features": ["dashboard", "user_management", "dashboard_customization", "reporting"],
                },
                "api_access": {
                    "enabled": True,
                    "api_keys": {"api_key": "premium-api-key"},
                    "limits": {"requests_per_minute": 100, "requests_per_day": 10000, "concurrent_connections": 5},
                    "enabled_features": ["rest_api", "authentication"],
                },
            }

        elif plan_type == PlanType.ENTERPRISE:
            return {
                "web_chat_app": {
                    "enabled": True,
                    "api_keys": {"iframe_api_key": "enterprise-iframe-key"},
                    "limits": {
                        "concurrent_sessions": -1,
                        "domains_allowed": -1,
                    },  # Unlimited
                    "enabled_features": [
                        "basic_chat",
                        "emoji_support",
                        "custom_css",
                        "file_upload",
                        "custom_branding",
                        "white_label",
                    ],
                },
                "whatsapp_app": {
                    "enabled": True,
                    "api_keys": {"whatsapp_api_key": "enterprise-whatsapp-key"},
                    "limits": {"messages_per_day": -1},  # Unlimited
                    "enabled_features": [
                        "auto_reply",
                        "business_hours",
                        "template_messages",
                        "media_messages",
                        "bulk_messaging",
                        "analytics",
                    ],
                },
                "management_app": {
                    "enabled": True,
                    "limits": {"max_users": -1, "max_organizations": -1, "storage_gb": -1},  # Unlimited
                    "enabled_features": ["dashboard", "user_management", "dashboard_customization", "reporting", "analytics"],
                },
                "api_access": {
                    "enabled": True,
                    "api_keys": {"api_key": "enterprise-api-key"},
                    "limits": {"requests_per_minute": -1, "requests_per_day": -1, "concurrent_connections": -1},  # Unlimited
                    "enabled_features": ["rest_api", "authentication", "webhooks", "bulk_operations"],
                },
            }

        return {}

    def update_description(self, description: str) -> "Plan":
        return self.model_copy(
            update={
                "description": description,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def update_pricing(self, pricing: Pricing) -> "Plan":
        return self.model_copy(
            update={"pricing": pricing, "updated_at": datetime.now(timezone.utc)}
        )

    def update_resource(self, resource_type: str, config: Dict[str, Any]) -> "Plan":
        new_resources = self.resources.copy()
        new_resources[resource_type] = config

        return self.model_copy(
            update={
                "resources": new_resources,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def enable_resource(self, resource_type: str) -> "Plan":
        new_resources = self.resources.copy()
        if resource_type in new_resources:
            new_resources[resource_type]["enabled"] = True

        return self.model_copy(
            update={
                "resources": new_resources,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def disable_resource(self, resource_type: str) -> "Plan":
        new_resources = self.resources.copy()
        if resource_type in new_resources:
            new_resources[resource_type]["enabled"] = False

        return self.model_copy(
            update={
                "resources": new_resources,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def deactivate(self) -> "Plan":
        return self.model_copy(
            update={
                "is_active": False,
                "status": PlanStatus.INACTIVE,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def activate(self) -> "Plan":
        return self.model_copy(
            update={
                "is_active": True,
                "status": PlanStatus.ACTIVE,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def deprecate(self) -> "Plan":
        return self.model_copy(
            update={
                "is_active": False,
                "status": PlanStatus.DEPRECATED,
                "is_public": False,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def has_resource(self, resource_type: str) -> bool:
        resource = self.resources.get(resource_type, {})
        return resource.get("enabled", False)

    def get_resource_config(self, resource_type: str) -> Dict[str, Any]:
        return self.resources.get(resource_type, {})

    def get_resource_api_key(self, resource_type: str, key_name: str) -> Optional[str]:
        resource = self.get_resource_config(resource_type)
        api_keys = resource.get("api_keys", {})
        return api_keys.get(key_name)

    def get_resource_limit(self, resource_type: str, limit_name: str) -> Optional[int]:
        resource = self.get_resource_config(resource_type)
        limits = resource.get("limits", {})
        return limits.get(limit_name)

    def get_resource_features(self, resource_type: str) -> list:
        resource = self.get_resource_config(resource_type)
        return resource.get("enabled_features", [])

    def get_feature_config(self, feature_key: str, default: Any = None) -> Any:
        """Get feature configuration from plan resources."""
        for resource_type, resource_config in self.resources.items():
            if resource_config.get("enabled", False):
                features = resource_config.get("enabled_features", [])
                if feature_key in features:
                    return resource_config.get("feature_configs", {}).get(feature_key, True)
        return default

    def get_limit(self, limit_key: str, default: int = 0) -> int:
        """Get limit value from plan resources."""
        for resource_type, resource_config in self.resources.items():
            if resource_config.get("enabled", False):
                limits = resource_config.get("limits", {})
                if limit_key in limits:
                    return limits[limit_key]
        return default

    def has_feature(self, feature_key: str) -> bool:
        """Check if plan has a specific feature enabled."""
        return self.get_feature_config(feature_key) is not None

    def is_feature_enabled(self, feature_key: str) -> bool:
        """Check if a specific feature is enabled."""
        feature_config = self.get_feature_config(feature_key, False)
        return bool(feature_config)

    def get_effective_limit(self, limit_key: str, override_value: Optional[int] = None) -> int:
        """Get effective limit considering plan defaults and overrides."""
        if override_value is not None:
            return override_value
        return self.get_limit(limit_key, 0)

    @property
    def features(self) -> Dict[str, Any]:
        """Get all features from all enabled resources."""
        all_features = {}
        for resource_type, resource_config in self.resources.items():
            if resource_config.get("enabled", False):
                features = resource_config.get("enabled_features", [])
                feature_configs = resource_config.get("feature_configs", {})
                for feature in features:
                    all_features[feature] = feature_configs.get(feature, True)
        return all_features

    @property
    def limits(self) -> Dict[str, int]:
        """Get all limits from all enabled resources."""
        all_limits = {}
        for resource_type, resource_config in self.resources.items():
            if resource_config.get("enabled", False):
                limits = resource_config.get("limits", {})
                all_limits.update(limits)
        return all_limits

    def can_support_users(self, user_count: int) -> bool:
        return user_count <= self.max_users

    def can_support_organizations(self, org_count: int) -> bool:
        return org_count <= self.max_organizations

    def has_whatsapp_app(self) -> bool:
        return self.has_resource("whatsapp_app")

    def has_web_chat_app(self) -> bool:
        return self.has_resource("web_chat_app")

    def has_management_app(self) -> bool:
        return self.has_resource("management_app")

    def has_api_access(self) -> bool:
        return self.has_resource("api_access")

    def is_available_for_signup(self) -> bool:
        return self.status == PlanStatus.ACTIVE and self.is_public and self.is_active

    def validate_resource_requirements(
        self, resource_type: str
    ) -> tuple[bool, list[str]]:
        """Validate if resource has required configuration."""
        errors = []
        resource = self.get_resource_config(resource_type)

        if not resource:
            errors.append(f"Resource {resource_type} not configured")
            return False, errors

        if not resource.get("enabled", False):
            errors.append(f"Resource {resource_type} is not enabled")

        # Validate required API keys
        api_keys = resource.get("api_keys", {})
        if resource_type == "whatsapp_app" and not api_keys.get("whatsapp_api_key"):
            errors.append("WhatsApp API key is required")

        if resource_type == "web_chat_app" and not api_keys.get("iframe_api_key"):
            errors.append("Iframe API key is required")

        if resource_type == "api_access" and not api_keys.get("api_key"):
            errors.append("API key is required")

        # Validate limits for management app
        if resource_type == "management_app":
            limits = resource.get("limits", {})
            if not limits.get("max_users"):
                errors.append("Max users limit is required for management app")

        return len(errors) == 0, errors
