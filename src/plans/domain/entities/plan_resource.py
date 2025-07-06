from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class PlanResourceType(str, Enum):
    WHATSAPP_APP = "whatsapp_app"
    WEB_CHAT_APP = "web_chat_app"
    MANAGEMENT_APP = "management_app"
    API_ACCESS = "api_access"
    DOCUMENT_STORAGE = "document_storage"
    CUSTOM = "custom"


class PlanResource(BaseModel):
    id: UUID
    plan_id: UUID
    resource_type: PlanResourceType
    configuration: Dict[str, Any]
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"frozen": True}

    @property
    def is_enabled(self) -> bool:
        """Compatibility property for is_enabled (maps to is_active)."""
        return self.is_active

    @is_enabled.setter
    def is_enabled(self, value: bool) -> None:
        """Compatibility setter for is_enabled (maps to is_active)."""
        # Note: This won't work with frozen=True, but we provide it for interface compatibility
        # The actual way to update would be through model_copy
        pass

    @classmethod
    def create(
        cls,
        plan_id: UUID,
        resource_type: PlanResourceType,
        configuration: Dict[str, Any],
    ) -> "PlanResource":
        return cls(
            id=uuid4(),
            plan_id=plan_id,
            resource_type=resource_type,
            configuration=configuration,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )

    @classmethod
    def create_resource(
        cls,
        plan_id: UUID,
        resource_type: PlanResourceType,
        configuration: Dict[str, Any],
        is_enabled: bool = True,
    ) -> "PlanResource":
        """Create resource with is_enabled parameter for compatibility."""
        return cls.create(
            plan_id=plan_id, resource_type=resource_type, configuration=configuration
        ).model_copy(update={"is_active": is_enabled})

    @classmethod
    def create_whatsapp_app_resource(
        cls,
        plan_id: UUID,
        api_key: str,
        messages_per_day: int = 1000,
        webhook_url: Optional[str] = None,
        auto_reply: bool = True,
    ) -> "PlanResource":
        """Create WhatsApp chat resource with standard configuration."""
        configuration = {
            "api_keys": {"whatsapp_api_key": api_key},
            "limits": {"messages_per_day": messages_per_day},
            "features": {
                "webhook_url": webhook_url,
                "auto_reply": auto_reply,
                "business_hours": True,
                "template_messages": True,
            },
        }

        return cls.create(
            plan_id=plan_id,
            resource_type=PlanResourceType.WHATSAPP_APP,
            configuration=configuration,
        )

    @classmethod
    def create_web_chat_app_resource(
        cls,
        plan_id: UUID,
        api_key: str,
        concurrent_sessions: int = 50,
        custom_css: bool = False,
        custom_branding: bool = False,
    ) -> "PlanResource":
        """Create iframe chat resource with standard configuration."""
        configuration = {
            "api_keys": {"iframe_api_key": api_key},
            "limits": {
                "concurrent_sessions": concurrent_sessions,
                "domains_allowed": 10,
            },
            "enabled_features": ["basic_chat", "file_upload", "emoji_support"],
        }

        if custom_css:
            configuration["enabled_features"].append("custom_css")

        if custom_branding:
            configuration["enabled_features"].extend(["custom_branding", "logo_upload"])

        return cls.create(
            plan_id=plan_id,
            resource_type=PlanResourceType.WEB_CHAT_APP,
            configuration=configuration,
        )

    @classmethod
    def create_management_app_resource(
        cls,
        plan_id: UUID,
        max_users: int = 10,
        max_organizations: int = 1,
        dashboard_features: bool = True,
        user_management: bool = True,
        analytics: bool = False,
    ) -> "PlanResource":
        """Create management app resource with standard configuration."""
        configuration = {
            "limits": {
                "max_users": max_users,
                "max_organizations": max_organizations,
                "storage_gb": 5,
            },
            "enabled_features": ["dashboard", "user_management"],
        }

        if dashboard_features:
            configuration["enabled_features"].extend(["dashboard_customization", "reporting"])

        if analytics:
            configuration["enabled_features"].append("analytics")

        return cls.create(
            plan_id=plan_id,
            resource_type=PlanResourceType.MANAGEMENT_APP,
            configuration=configuration,
        )

    @classmethod
    def create_api_access_resource(
        cls,
        plan_id: UUID,
        api_key: str,
        requests_per_minute: int = 100,
        requests_per_day: int = 10000,
        webhook_support: bool = False,
        bulk_operations: bool = False,
    ) -> "PlanResource":
        """Create API access resource with standard configuration."""
        configuration = {
            "api_keys": {"api_key": api_key},
            "limits": {
                "requests_per_minute": requests_per_minute,
                "requests_per_day": requests_per_day,
                "concurrent_connections": 5,
            },
            "enabled_features": ["rest_api", "authentication"],
        }

        if webhook_support:
            configuration["enabled_features"].append("webhooks")

        if bulk_operations:
            configuration["enabled_features"].append("bulk_operations")

        return cls.create(
            plan_id=plan_id,
            resource_type=PlanResourceType.API_ACCESS,
            configuration=configuration,
        )

    @classmethod
    def create_document_storage_resource(
        cls,
        plan_id: UUID,
        max_documents: int = 100,
        max_storage_gb: int = 5,
        ai_training_enabled: bool = True,
        ai_query_enabled: bool = True,
        document_sharing: bool = True,
        advanced_permissions: bool = False,
        supported_formats: list[str] = None,
    ) -> "PlanResource":
        """Create document storage resource with standard configuration."""
        if supported_formats is None:
            supported_formats = ["pdf", "txt", "docx", "md"]
        
        configuration = {
            "limits": {
                "max_documents": max_documents,
                "max_storage_gb": max_storage_gb,
                "max_file_size_mb": 50,
                "max_documents_per_upload": 10,
            },
            "enabled_features": [
                "document_upload",
                "document_download",
                "document_preview",
                "basic_search",
            ],
            "document_settings": {
                "supported_formats": supported_formats,
                "auto_indexing": True,
                "version_control": False,
                "retention_days": None,  # No automatic deletion
            },
            "ai_features": {
                "ai_training_enabled": ai_training_enabled,
                "ai_query_enabled": ai_query_enabled,
                "auto_chunking": True,
                "semantic_search": ai_query_enabled,
            },
            "permission_features": {
                "document_sharing": document_sharing,
                "role_based_access": True,
                "user_based_access": advanced_permissions,
                "confidentiality_levels": advanced_permissions,
                "time_based_access": advanced_permissions,
            },
        }

        # Add advanced features based on parameters
        if document_sharing:
            configuration["enabled_features"].extend([
                "document_sharing",
                "share_links",
            ])

        if advanced_permissions:
            configuration["enabled_features"].extend([
                "advanced_permissions",
                "audit_logging",
                "permission_templates",
            ])

        if ai_training_enabled or ai_query_enabled:
            configuration["enabled_features"].extend([
                "ai_integration",
                "vector_storage",
            ])

        return cls.create(
            plan_id=plan_id,
            resource_type=PlanResourceType.DOCUMENT_STORAGE,
            configuration=configuration,
        )

    def update_configuration(self, new_configuration: Dict[str, Any]) -> "PlanResource":
        """Update resource configuration."""
        merged_config = self.configuration.copy()
        merged_config.update(new_configuration)

        return self.model_copy(
            update={
                "configuration": merged_config,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def update_api_key(self, key_name: str, api_key: str) -> "PlanResource":
        """Update specific API key in configuration."""
        new_config = self.configuration.copy()
        if "api_keys" not in new_config:
            new_config["api_keys"] = {}

        new_config["api_keys"][key_name] = api_key

        return self.model_copy(
            update={
                "configuration": new_config,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def update_limit(self, limit_name: str, value: int) -> "PlanResource":
        """Update specific limit in configuration."""
        new_config = self.configuration.copy()
        if "limits" not in new_config:
            new_config["limits"] = {}

        new_config["limits"][limit_name] = value

        return self.model_copy(
            update={
                "configuration": new_config,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def add_enabled_feature(self, feature: str) -> "PlanResource":
        """Add feature to enabled features list."""
        new_config = self.configuration.copy()
        if "enabled_features" not in new_config:
            new_config["enabled_features"] = []

        if feature not in new_config["enabled_features"]:
            new_config["enabled_features"].append(feature)

        return self.model_copy(
            update={
                "configuration": new_config,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def remove_enabled_feature(self, feature: str) -> "PlanResource":
        """Remove feature from enabled features list."""
        new_config = self.configuration.copy()
        if (
            "enabled_features" in new_config
            and feature in new_config["enabled_features"]
        ):
            new_config["enabled_features"].remove(feature)

        return self.model_copy(
            update={
                "configuration": new_config,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def activate(self) -> "PlanResource":
        """Activate resource."""
        return self.model_copy(
            update={"is_active": True, "updated_at": datetime.now(timezone.utc)}
        )

    def deactivate(self) -> "PlanResource":
        """Deactivate resource."""
        return self.model_copy(
            update={"is_active": False, "updated_at": datetime.now(timezone.utc)}
        )

    def get_api_key(self, key_name: str) -> Optional[str]:
        """Get specific API key from configuration."""
        api_keys = self.configuration.get("api_keys", {})
        return api_keys.get(key_name)

    def get_limit(self, limit_name: str) -> Optional[int]:
        """Get specific limit from configuration."""
        limits = self.configuration.get("limits", {})
        return limits.get(limit_name)

    def get_enabled_features(self) -> list[str]:
        """Get list of enabled features."""
        return self.configuration.get("enabled_features", [])

    def has_feature(self, feature: str) -> bool:
        """Check if specific feature is enabled."""
        return feature in self.get_enabled_features()

    # Document storage specific methods
    def get_document_setting(self, setting_name: str) -> Any:
        """Get specific document setting from configuration."""
        doc_settings = self.configuration.get("document_settings", {})
        return doc_settings.get(setting_name)

    def get_ai_feature_setting(self, setting_name: str) -> Any:
        """Get specific AI feature setting from configuration."""
        ai_features = self.configuration.get("ai_features", {})
        return ai_features.get(setting_name)

    def get_permission_feature_setting(self, setting_name: str) -> Any:
        """Get specific permission feature setting from configuration."""
        permission_features = self.configuration.get("permission_features", {})
        return permission_features.get(setting_name)

    def is_ai_training_enabled(self) -> bool:
        """Check if AI training is enabled for documents."""
        return self.get_ai_feature_setting("ai_training_enabled") is True

    def is_ai_query_enabled(self) -> bool:
        """Check if AI query is enabled for documents."""
        return self.get_ai_feature_setting("ai_query_enabled") is True

    def is_document_sharing_enabled(self) -> bool:
        """Check if document sharing is enabled."""
        return self.get_permission_feature_setting("document_sharing") is True

    def supports_advanced_permissions(self) -> bool:
        """Check if advanced permissions are supported."""
        return self.get_permission_feature_setting("user_based_access") is True

    def get_supported_document_formats(self) -> list[str]:
        """Get list of supported document formats."""
        return self.get_document_setting("supported_formats") or []

    def supports_document_format(self, format_name: str) -> bool:
        """Check if specific document format is supported."""
        return format_name.lower() in [fmt.lower() for fmt in self.get_supported_document_formats()]

    def get_max_documents(self) -> int:
        """Get maximum number of documents allowed."""
        return self.get_limit("max_documents") or 0

    def get_max_storage_gb(self) -> int:
        """Get maximum storage in GB."""
        return self.get_limit("max_storage_gb") or 0

    def get_max_file_size_mb(self) -> int:
        """Get maximum file size in MB."""
        return self.get_limit("max_file_size_mb") or 50

    def update_document_limits(
        self,
        max_documents: Optional[int] = None,
        max_storage_gb: Optional[int] = None,
        max_file_size_mb: Optional[int] = None
    ) -> "PlanResource":
        """Update document storage limits."""
        new_config = self.configuration.copy()
        if "limits" not in new_config:
            new_config["limits"] = {}

        if max_documents is not None:
            new_config["limits"]["max_documents"] = max_documents
        if max_storage_gb is not None:
            new_config["limits"]["max_storage_gb"] = max_storage_gb
        if max_file_size_mb is not None:
            new_config["limits"]["max_file_size_mb"] = max_file_size_mb

        return self.model_copy(
            update={
                "configuration": new_config,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def enable_ai_feature(self, feature_name: str, enabled: bool = True) -> "PlanResource":
        """Enable or disable specific AI feature."""
        new_config = self.configuration.copy()
        if "ai_features" not in new_config:
            new_config["ai_features"] = {}

        new_config["ai_features"][feature_name] = enabled

        return self.model_copy(
            update={
                "configuration": new_config,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def enable_permission_feature(self, feature_name: str, enabled: bool = True) -> "PlanResource":
        """Enable or disable specific permission feature."""
        new_config = self.configuration.copy()
        if "permission_features" not in new_config:
            new_config["permission_features"] = {}

        new_config["permission_features"][feature_name] = enabled

        return self.model_copy(
            update={
                "configuration": new_config,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def is_valid_configuration(self) -> tuple[bool, list[str]]:
        """Validate resource configuration."""
        errors = []

        # Validate based on resource type
        if self.resource_type == PlanResourceType.WHATSAPP_APP:
            if not self.get_api_key("whatsapp_api_key"):
                errors.append("WhatsApp API key is required")

            if not self.get_limit("messages_per_day"):
                errors.append("Messages per day limit is required")

        elif self.resource_type == PlanResourceType.WEB_CHAT_APP:
            if not self.get_api_key("iframe_api_key"):
                errors.append("Iframe API key is required")

            if not self.get_limit("concurrent_sessions"):
                errors.append("Concurrent sessions limit is required")

        elif self.resource_type == PlanResourceType.MANAGEMENT_APP:
            # Management app typically doesn't need API keys
            if not self.get_limit("max_users"):
                errors.append("Max users limit is required")

        elif self.resource_type == PlanResourceType.API_ACCESS:
            if not self.get_api_key("api_key"):
                errors.append("API key is required")

            if not self.get_limit("requests_per_minute"):
                errors.append("Requests per minute limit is required")

        elif self.resource_type == PlanResourceType.DOCUMENT_STORAGE:
            if not self.get_limit("max_documents"):
                errors.append("Max documents limit is required")

            if not self.get_limit("max_storage_gb"):
                errors.append("Max storage limit is required")

            # Validate document settings
            doc_settings = self.configuration.get("document_settings", {})
            if not doc_settings.get("supported_formats"):
                errors.append("Supported document formats must be specified")

        return len(errors) == 0, errors

    def get_resource_summary(self) -> Dict[str, Any]:
        """Get summary of resource configuration."""
        return {
            "id": str(self.id),
            "resource_type": self.resource_type.value,
            "is_active": self.is_active,
            "api_keys_count": len(self.configuration.get("api_keys", {})),
            "limits": self.configuration.get("limits", {}),
            "enabled_features": self.get_enabled_features(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
