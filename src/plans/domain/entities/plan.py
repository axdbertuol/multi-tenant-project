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
                "chat_iframe": {
                    "enabled": True,
                    "api_keys": {"iframe_api_key": "basic-iframe-key"},
                    "limits": {"concurrent_sessions": 25, "domains_allowed": 3},
                    "enabled_features": ["basic_chat", "emoji_support"],
                },
                "chat_whatsapp": {
                    "enabled": True,
                    "api_keys": {"whatsapp_api_key": "basic-whatsapp-key"},
                    "limits": {"messages_per_day": 1000},
                    "enabled_features": ["auto_reply", "business_hours"],
                },
            }

        elif plan_type == PlanType.PREMIUM:
            return {
                "chat_iframe": {
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
                "chat_whatsapp": {
                    "enabled": True,
                    "api_keys": {"whatsapp_api_key": "premium-whatsapp-key"},
                    "limits": {"messages_per_day": 5000},
                    "enabled_features": [
                        "auto_reply",
                        "business_hours",
                        "template_messages",
                        "media_messages",
                    ],
                },
            }

        elif plan_type == PlanType.ENTERPRISE:
            return {
                "chat_iframe": {
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
                "chat_whatsapp": {
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

    def can_support_users(self, user_count: int) -> bool:
        return user_count <= self.max_users

    def can_support_organizations(self, org_count: int) -> bool:
        return org_count <= self.max_organizations

    def has_chat_whatsapp(self) -> bool:
        return self.has_resource("chat_whatsapp")

    def has_chat_iframe(self) -> bool:
        return self.has_resource("chat_iframe")

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
        if resource_type == "chat_whatsapp" and not api_keys.get("whatsapp_api_key"):
            errors.append("WhatsApp API key is required")

        if resource_type == "chat_iframe" and not api_keys.get("iframe_api_key"):
            errors.append("Iframe API key is required")

        return len(errors) == 0, errors
