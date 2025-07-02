from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, field_validator


class PlanConfiguration(BaseModel):
    id: UUID
    plan_id: UUID
    api_keys: Dict[str, str]
    limits: Dict[str, int]
    enabled_features: List[str]
    custom_settings: Dict[str, Any]
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        plan_id: UUID,
        api_keys: Optional[Dict[str, str]] = None,
        limits: Optional[Dict[str, int]] = None,
        enabled_features: Optional[List[str]] = None,
        custom_settings: Optional[Dict[str, Any]] = None,
    ) -> "PlanConfiguration":
        return cls(
            id=uuid4(),
            plan_id=plan_id,
            api_keys=api_keys or {},
            limits=limits or {},
            enabled_features=enabled_features or [],
            custom_settings=custom_settings or {},
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )

    @classmethod
    def create_basic_configuration(cls, plan_id: UUID) -> "PlanConfiguration":
        """Create basic plan configuration."""
        return cls.create(
            plan_id=plan_id,
            limits={
                "monthly_messages": 10000,
                "monthly_api_calls": 50000,
                "storage_mb": 1000,
                "concurrent_sessions": 25,
            },
            enabled_features=[
                "chat_iframe",
                "chat_whatsapp",
                "webhook_support",
                "basic_analytics",
            ],
        )

    @classmethod
    def create_premium_configuration(cls, plan_id: UUID) -> "PlanConfiguration":
        """Create premium plan configuration."""
        return cls.create(
            plan_id=plan_id,
            api_keys={
                "whatsapp_api_key": "premium-whatsapp-key",
                "iframe_api_key": "premium-iframe-key",
            },
            limits={
                "monthly_messages": 100000,
                "monthly_api_calls": 500000,
                "storage_mb": 10000,
                "concurrent_sessions": 100,
                "webhook_endpoints": 10,
            },
            enabled_features=[
                "chat_iframe",
                "chat_whatsapp",
                "custom_branding",
                "webhook_support",
                "advanced_analytics",
                "custom_css",
                "priority_support",
            ],
        )

    @classmethod
    def create_enterprise_configuration(cls, plan_id: UUID) -> "PlanConfiguration":
        """Create enterprise plan configuration."""
        return cls.create(
            plan_id=plan_id,
            api_keys={
                "whatsapp_api_key": "enterprise-whatsapp-key",
                "iframe_api_key": "enterprise-iframe-key",
                "sso_api_key": "enterprise-sso-key",
            },
            limits={
                "monthly_messages": -1,  # Unlimited
                "monthly_api_calls": -1,  # Unlimited
                "storage_mb": -1,  # Unlimited
                "concurrent_sessions": -1,  # Unlimited
                "webhook_endpoints": -1,  # Unlimited
                "custom_fields": -1,  # Unlimited
            },
            enabled_features=[
                "chat_iframe",
                "chat_whatsapp",
                "custom_branding",
                "webhook_support",
                "advanced_analytics",
                "custom_css",
                "priority_support",
                "sso",
                "audit_logs",
                "white_label",
                "dedicated_support",
            ],
        )

    def update_api_key(self, key_name: str, api_key: str) -> "PlanConfiguration":
        """Update or add an API key."""
        new_api_keys = self.api_keys.copy()
        new_api_keys[key_name] = api_key

        return self.model_copy(
            update={"api_keys": new_api_keys, "updated_at": datetime.now(timezone.utc)}
        )

    def remove_api_key(self, key_name: str) -> "PlanConfiguration":
        """Remove an API key."""
        new_api_keys = self.api_keys.copy()
        new_api_keys.pop(key_name, None)

        return self.model_copy(
            update={"api_keys": new_api_keys, "updated_at": datetime.now(timezone.utc)}
        )

    def update_limit(self, limit_name: str, value: int) -> "PlanConfiguration":
        """Update or add a limit."""
        new_limits = self.limits.copy()
        new_limits[limit_name] = value

        return self.model_copy(
            update={"limits": new_limits, "updated_at": datetime.now(timezone.utc)}
        )

    def remove_limit(self, limit_name: str) -> "PlanConfiguration":
        """Remove a limit."""
        new_limits = self.limits.copy()
        new_limits.pop(limit_name, None)

        return self.model_copy(
            update={"limits": new_limits, "updated_at": datetime.now(timezone.utc)}
        )

    def add_feature(self, feature: str) -> "PlanConfiguration":
        """Add a feature to enabled features."""
        if feature not in self.enabled_features:
            new_features = self.enabled_features.copy()
            new_features.append(feature)

            return self.model_copy(
                update={
                    "enabled_features": new_features,
                    "updated_at": datetime.now(timezone.utc),
                }
            )

        return self

    def remove_feature(self, feature: str) -> "PlanConfiguration":
        """Remove a feature from enabled features."""
        if feature in self.enabled_features:
            new_features = self.enabled_features.copy()
            new_features.remove(feature)

            return self.model_copy(
                update={
                    "enabled_features": new_features,
                    "updated_at": datetime.now(timezone.utc),
                }
            )

        return self

    def update_custom_setting(self, key: str, value: Any) -> "PlanConfiguration":
        """Update or add a custom setting."""
        new_settings = self.custom_settings.copy()
        new_settings[key] = value

        return self.model_copy(
            update={
                "custom_settings": new_settings,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def remove_custom_setting(self, key: str) -> "PlanConfiguration":
        """Remove a custom setting."""
        new_settings = self.custom_settings.copy()
        new_settings.pop(key, None)

        return self.model_copy(
            update={
                "custom_settings": new_settings,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def bulk_update(
        self,
        api_keys: Optional[Dict[str, str]] = None,
        limits: Optional[Dict[str, int]] = None,
        enabled_features: Optional[List[str]] = None,
        custom_settings: Optional[Dict[str, Any]] = None,
    ) -> "PlanConfiguration":
        """Bulk update configuration."""
        updates = {"updated_at": datetime.now(timezone.utc)}

        if api_keys is not None:
            new_api_keys = self.api_keys.copy()
            new_api_keys.update(api_keys)
            updates["api_keys"] = new_api_keys

        if limits is not None:
            new_limits = self.limits.copy()
            new_limits.update(limits)
            updates["limits"] = new_limits

        if enabled_features is not None:
            updates["enabled_features"] = enabled_features

        if custom_settings is not None:
            new_settings = self.custom_settings.copy()
            new_settings.update(custom_settings)
            updates["custom_settings"] = new_settings

        return self.model_copy(update=updates)

    def activate(self) -> "PlanConfiguration":
        """Activate configuration."""
        return self.model_copy(
            update={"is_active": True, "updated_at": datetime.now(timezone.utc)}
        )

    def deactivate(self) -> "PlanConfiguration":
        """Deactivate configuration."""
        return self.model_copy(
            update={"is_active": False, "updated_at": datetime.now(timezone.utc)}
        )

    def get_api_key(self, key_name: str) -> Optional[str]:
        """Get specific API key."""
        return self.api_keys.get(key_name)

    def get_limit(self, limit_name: str) -> Optional[int]:
        """Get specific limit."""
        return self.limits.get(limit_name)

    def has_feature(self, feature: str) -> bool:
        """Check if feature is enabled."""
        return feature in self.enabled_features

    def get_custom_setting(self, key: str, default: Any = None) -> Any:
        """Get custom setting value."""
        return self.custom_settings.get(key, default)

    def is_limit_unlimited(self, limit_name: str) -> bool:
        """Check if limit is unlimited (-1)."""
        limit = self.get_limit(limit_name)
        return limit == -1 if limit is not None else False

    def has_required_api_keys_for_chat_whatsapp(self) -> bool:
        """Check if required API keys for WhatsApp are present."""
        return self.get_api_key("whatsapp_api_key") is not None

    def has_required_api_keys_for_chat_iframe(self) -> bool:
        """Check if required API keys for iframe chat are present."""
        return self.get_api_key("iframe_api_key") is not None

    def validate_configuration(self) -> tuple[bool, List[str]]:
        """Validate the configuration."""
        errors = []

        # Check for required API keys if features are enabled
        if (
            self.has_feature("chat_whatsapp")
            and not self.has_required_api_keys_for_chat_whatsapp()
        ):
            errors.append(
                "WhatsApp API key is required when chat_whatsapp feature is enabled"
            )

        if (
            self.has_feature("chat_iframe")
            and not self.has_required_api_keys_for_chat_iframe()
        ):
            errors.append(
                "Iframe API key is required when chat_iframe feature is enabled"
            )

        # Check for negative limits (except -1 for unlimited)
        for limit_name, limit_value in self.limits.items():
            if limit_value < -1:
                errors.append(f"Invalid limit value for {limit_name}: {limit_value}")

        return len(errors) == 0, errors

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the configuration."""
        return {
            "id": str(self.id),
            "plan_id": str(self.plan_id),
            "api_keys_count": len(self.api_keys),
            "api_key_names": list(self.api_keys.keys()),
            "limits": self.limits,
            "enabled_features": self.enabled_features,
            "custom_settings_count": len(self.custom_settings),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (hiding sensitive API keys)."""
        return {
            "id": str(self.id),
            "plan_id": str(self.plan_id),
            "api_keys": {k: "***" for k in self.api_keys.keys()},  # Hide actual keys
            "limits": self.limits,
            "enabled_features": self.enabled_features,
            "custom_settings": self.custom_settings,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
