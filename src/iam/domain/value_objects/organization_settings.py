from pydantic import BaseModel, field_validator
from typing import Dict, Any


class OrganizationSettings(BaseModel):
    max_users: int
    allow_user_registration: bool
    require_email_verification: bool
    session_timeout_hours: int
    features_enabled: Dict[str, bool]
    custom_settings: Dict[str, Any]

    model_config = {"frozen": True}

    @field_validator("max_users")
    @classmethod
    def validate_max_users(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Maximum users must be at least 1")
        if v > 10000:
            raise ValueError("Maximum users cannot exceed 10,000")
        return v

    @field_validator("session_timeout_hours")
    @classmethod
    def validate_session_timeout(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Session timeout must be at least 1 hour")
        if v > 720:  # 30 days
            raise ValueError("Session timeout cannot exceed 720 hours (30 days)")
        return v

    @classmethod
    def create_default(cls, max_users: int = 10) -> "OrganizationSettings":
        return cls(
            max_users=max_users,
            allow_user_registration=True,
            require_email_verification=True,
            session_timeout_hours=24,
            features_enabled={
                "chat_whatsapp": False,
                "chat_iframe": False,
                "api_access": True,
                "custom_branding": False,
                "analytics": True,
            },
            custom_settings={},
        )

    def enable_feature(self, feature_name: str) -> "OrganizationSettings":
        """Enable a specific feature."""
        new_features = self.features_enabled.copy()
        new_features[feature_name] = True

        return self.model_copy(update={"features_enabled": new_features})

    def disable_feature(self, feature_name: str) -> "OrganizationSettings":
        """Disable a specific feature."""
        new_features = self.features_enabled.copy()
        new_features[feature_name] = False

        return self.model_copy(update={"features_enabled": new_features})

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return self.features_enabled.get(feature_name, False)

    def update_max_users(self, new_max: int) -> "OrganizationSettings":
        """Update maximum users limit."""
        return self.model_copy(update={"max_users": new_max})

    def update_custom_setting(self, key: str, value: Any) -> "OrganizationSettings":
        """Update a custom setting."""
        new_custom = self.custom_settings.copy()
        new_custom[key] = value

        return self.model_copy(update={"custom_settings": new_custom})

    def get_custom_setting(self, key: str, default: Any = None) -> Any:
        """Get a custom setting value."""
        return self.custom_settings.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for JSON serialization."""
        return {
            "max_users": self.max_users,
            "allow_user_registration": self.allow_user_registration,
            "require_email_verification": self.require_email_verification,
            "session_timeout_hours": self.session_timeout_hours,
            "features_enabled": self.features_enabled.copy(),
            "custom_settings": self.custom_settings.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrganizationSettings":
        """Create OrganizationSettings from dictionary (for JSON deserialization)."""
        return cls(
            max_users=data.get("max_users", 10),
            allow_user_registration=data.get("allow_user_registration", True),
            require_email_verification=data.get("require_email_verification", True),
            session_timeout_hours=data.get("session_timeout_hours", 24),
            features_enabled=data.get("features_enabled", {}),
            custom_settings=data.get("custom_settings", {}),
        )

    def model_dump(self) -> Dict[str, Any]:
        """Alias for to_dict() for compatibility with DTOs."""
        return self.to_dict()
