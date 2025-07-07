from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import json


class ApplicationInstance(BaseModel):
    id: UUID
    plan_resource_id: UUID
    organization_id: UUID
    instance_name: str = Field(..., min_length=1, max_length=200)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    api_keys: Dict[str, Any] = Field(default_factory=dict)  # Encrypted API keys
    limits_override: Dict[str, int] = Field(
        default_factory=dict
    )  # Custom limits for this instance
    is_active: bool = True
    owner_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        plan_resource_id: UUID,
        organization_id: UUID,
        instance_name: str,
        owner_id: UUID,
        configuration: Optional[Dict[str, Any]] = None,
        api_keys: Optional[Dict[str, Any]] = None,
        limits_override: Optional[Dict[str, int]] = None,
    ) -> "ApplicationInstance":
        """Create a new application instance."""
        now = datetime.utcnow()

        return cls(
            id=uuid4(),
            plan_resource_id=plan_resource_id,
            organization_id=organization_id,
            instance_name=instance_name,
            configuration=configuration or {},
            api_keys=api_keys or {},
            limits_override=limits_override or {},
            is_active=True,
            owner_id=owner_id,
            created_at=now,
        )

    def update_name(self, instance_name: str) -> "ApplicationInstance":
        """Update the instance name."""
        if not instance_name or len(instance_name) < 1 or len(instance_name) > 200:
            raise ValueError("Instance name must be between 1 and 200 characters")

        return self.model_copy(
            update={
                "instance_name": instance_name,
                "updated_at": datetime.utcnow(),
            }
        )

    def update_configuration(
        self, configuration: Dict[str, Any]
    ) -> "ApplicationInstance":
        """Update the instance configuration."""
        if not isinstance(configuration, dict):
            raise ValueError("Configuration must be a dictionary")

        return self.model_copy(
            update={
                "configuration": configuration,
                "updated_at": datetime.utcnow(),
            }
        )

    def update_config_value(self, key: str, value: Any) -> "ApplicationInstance":
        """Update a specific configuration value."""
        new_config = self.configuration.copy()
        new_config[key] = value

        return self.model_copy(
            update={
                "configuration": new_config,
                "updated_at": datetime.utcnow(),
            }
        )

    def remove_config_value(self, key: str) -> "ApplicationInstance":
        """Remove a specific configuration value."""
        new_config = self.configuration.copy()
        new_config.pop(key, None)

        return self.model_copy(
            update={
                "configuration": new_config,
                "updated_at": datetime.utcnow(),
            }
        )

    def set_api_key(self, key_name: str, encrypted_key: str) -> "ApplicationInstance":
        """Set an encrypted API key."""
        new_keys = self.api_keys.copy()
        new_keys[key_name] = encrypted_key

        return self.model_copy(
            update={
                "api_keys": new_keys,
                "updated_at": datetime.utcnow(),
            }
        )

    def remove_api_key(self, key_name: str) -> "ApplicationInstance":
        """Remove an API key."""
        new_keys = self.api_keys.copy()
        new_keys.pop(key_name, None)

        return self.model_copy(
            update={
                "api_keys": new_keys,
                "updated_at": datetime.utcnow(),
            }
        )

    def set_limit_override(
        self, limit_key: str, limit_value: int
    ) -> "ApplicationInstance":
        """Set a custom limit override."""
        if limit_value < -1:
            raise ValueError("Limit value must be -1 (unlimited) or positive")

        new_limits = self.limits_override.copy()
        new_limits[limit_key] = limit_value

        return self.model_copy(
            update={
                "limits_override": new_limits,
                "updated_at": datetime.utcnow(),
            }
        )

    def remove_limit_override(self, limit_key: str) -> "ApplicationInstance":
        """Remove a custom limit override."""
        new_limits = self.limits_override.copy()
        new_limits.pop(limit_key, None)

        return self.model_copy(
            update={
                "limits_override": new_limits,
                "updated_at": datetime.utcnow(),
            }
        )

    def deactivate(self) -> "ApplicationInstance":
        """Deactivate the application instance."""
        return self.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.utcnow(),
            }
        )

    def reactivate(self) -> "ApplicationInstance":
        """Reactivate the application instance."""
        return self.model_copy(
            update={
                "is_active": True,
                "updated_at": datetime.utcnow(),
            }
        )

    def change_owner(self, new_owner_id: UUID) -> "ApplicationInstance":
        """Change the instance owner."""
        return self.model_copy(
            update={
                "owner_id": new_owner_id,
                "updated_at": datetime.utcnow(),
            }
        )

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.configuration.get(key, default)

    def has_config_value(self, key: str) -> bool:
        """Check if a configuration value exists."""
        return key in self.configuration

    def has_api_key(self, key_name: str) -> bool:
        """Check if an API key exists."""
        return key_name in self.api_keys

    def get_effective_limit(self, limit_key: str, plan_default: int) -> int:
        """Get the effective limit value considering overrides."""
        return self.limits_override.get(limit_key, plan_default)

    def has_limit_override(self, limit_key: str) -> bool:
        """Check if a limit override exists."""
        return limit_key in self.limits_override

    def is_limit_unlimited(self, limit_key: str, plan_default: int) -> bool:
        """Check if a limit is unlimited."""
        effective_limit = self.get_effective_limit(limit_key, plan_default)
        return effective_limit == -1

    def can_be_used(self) -> tuple[bool, str]:
        """Check if the instance can be used."""
        if not self.is_active:
            return False, "Application instance is deactivated"

        return True, "Application instance is available"

    def get_display_name(self) -> str:
        """Get formatted display name."""
        status = "Active" if self.is_active else "Inactive"
        return f"{self.instance_name} ({status})"

    def validate_configuration(self) -> tuple[bool, str]:
        """Validate the instance configuration."""
        try:
            # Check if configuration is serializable
            json.dumps(self.configuration)
            return True, "Configuration is valid"
        except (TypeError, ValueError) as e:
            return False, f"Configuration is not valid JSON: {str(e)}"

    def get_api_key_names(self) -> list[str]:
        """Get list of API key names (not the keys themselves)."""
        return list(self.api_keys.keys())

    def get_limit_override_keys(self) -> list[str]:
        """Get list of limit override keys."""
        return list(self.limits_override.keys())

    def get_instance_summary(self) -> Dict[str, Any]:
        """Get a summary of the application instance."""
        return {
            "id": str(self.id),
            "plan_resource_id": str(self.plan_resource_id),
            "organization_id": str(self.organization_id),
            "instance_name": self.instance_name,
            "is_active": self.is_active,
            "owner_id": str(self.owner_id),
            "display_name": self.get_display_name(),
            "config_keys": list(self.configuration.keys()),
            "api_key_names": self.get_api_key_names(),
            "limit_override_keys": self.get_limit_override_keys(),
            "has_custom_limits": len(self.limits_override) > 0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
