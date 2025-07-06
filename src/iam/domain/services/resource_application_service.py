"""Service for managing applications as resources."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..entities.resource import Resource
from ..repositories.resource_repository import ResourceRepository
from ...application.dtos.resource_dto import ResourceCreateDTO
from ....shared.infrastructure.config import get_configuration_loader


class ApplicationResourceService:
    """
    Service for managing applications as special resource types.
    
    This approach treats applications as resources with specific attributes,
    leveraging the existing RBAC/ABAC system for permissions.
    """
    
    def __init__(self, resource_repository: Optional[ResourceRepository] = None):
        """Initialize with optional resource repository for persistence operations."""
        self._resource_repository = resource_repository
        self._config_loader = get_configuration_loader()
    
    def _get_application_resource_types(self) -> Dict[str, Dict]:
        """Get application resource types from configuration."""
        try:
            return self._config_loader.load_application_types()
        except Exception:
            # Fallback to hardcoded types
            return {
                "web_chat_app": {
                    "name": "Web Chat Application",
                    "description": "Live chat widget for websites",
                    "icon": "chat-bubble",
                    "category": "customer_support",
                    "default_features": [
                        "live_chat",
                        "chat_history", 
                        "basic_customization"
                    ],
                    "required_permissions": [
                        "conversation:read",
                        "conversation:create",
                        "message:send",
                        "message:receive"
                    ]
                },
                "management_app": {
                    "name": "Management Dashboard", 
                    "description": "Organization and user management dashboard",
                    "icon": "dashboard",
                    "category": "administration",
                    "default_features": [
                        "user_management",
                        "organization_settings",
                        "basic_analytics"
                    ],
                    "required_permissions": [
                        "user:read",
                        "organization:read",
                        "organization:configure"
                    ]
                },
                "whatsapp_app": {
                    "name": "WhatsApp Integration",
                    "description": "WhatsApp Business API integration",
                    "icon": "whatsapp",
                    "category": "messaging",
                    "default_features": [
                        "whatsapp_messaging",
                        "template_management",
                        "contact_sync"
                    ],
                    "required_permissions": [
                        "whatsapp:send",
                        "whatsapp:receive",
                        "whatsapp:configure"
                    ]
                },
                "api_access": {
                    "name": "API Access",
                    "description": "Programmatic access to platform features",
                    "icon": "api",
                    "category": "integration", 
                    "default_features": [
                        "rest_api",
                        "webhook_management"
                    ],
                    "required_permissions": [
                        "api:read",
                        "api:write",
                        "webhook:configure"
                    ]
                },
                "document_storage": {
                    "name": "Document Storage",
                    "description": "AI-powered document management and search",
                    "icon": "document",
                    "category": "content_management",
                    "default_features": [
                        "document_upload",
                        "document_download",
                        "basic_search",
                        "ai_query"
                    ],
                    "required_permissions": [
                        "document:read",
                        "document:create",
                        "document:update",
                        "document:delete",
                        "document:ai_query"
                    ]
                }
            }
    
    def create_application_resource(
        self,
        app_type: str,
        organization_id: UUID,
        owner_id: UUID,
        plan_features: Optional[List[str]] = None,
        custom_config: Optional[Dict] = None
    ) -> Resource:
        """
        Create an application resource for an organization.
        
        Args:
            app_type: Type of application (web_chat_app, management_app, etc.)
            organization_id: Organization that owns this application
            owner_id: User who created/owns the application
            plan_features: Features enabled by subscription plan
            custom_config: Additional configuration
            
        Returns:
            Resource representing the application
        """
        application_types = self._get_application_resource_types()
        if app_type not in application_types:
            raise ValueError(f"Unknown application type: {app_type}")
        
        app_config = application_types[app_type]
        
        # Determine enabled features based on plan
        enabled_features = app_config["default_features"].copy()
        if plan_features:
            # Only enable features that are in the plan
            enabled_features = [f for f in enabled_features if f in plan_features]
        
        # Build application attributes
        attributes = {
            "app_name": app_config["name"],
            "app_description": app_config["description"],
            "app_icon": app_config["icon"],
            "app_category": app_config["category"],
            "enabled_features": enabled_features,
            "required_permissions": app_config["required_permissions"],
            "status": "active",
            "created_date": datetime.now(timezone.utc).isoformat(),
        }
        
        # Add app-specific default configurations
        app_specific_config = self._config_loader.get_default_app_configuration(app_type, str(organization_id))
        attributes.update(app_specific_config)
        
        # Add custom configuration (overrides defaults)
        if custom_config:
            attributes.update(custom_config)
        
        # Create resource representing the application
        return Resource.create(
            resource_type=app_type,
            resource_id=organization_id,  # App instance per organization
            owner_id=owner_id,
            organization_id=organization_id,
            attributes=attributes
        )
    
    def get_organization_applications(
        self,
        organization_id: UUID
    ) -> List[Resource]:
        """
        Get all application resources for an organization.
        
        This queries the resource repository for application types.
        """
        if not self._resource_repository:
            return []
        
        # Get all resources for the organization
        org_resources = self._resource_repository.get_by_organization_id(organization_id)
        
        # Filter for application resources (ending with _app or document_storage)
        app_resources = []
        for resource in org_resources:
            if (resource.resource_type.endswith("_app") or 
                resource.resource_type == "document_storage"):
                app_resources.append(resource)
        
        return app_resources
    
    def is_application_resource(self, resource: Resource) -> bool:
        """Check if a resource represents an application."""
        return resource.resource_type.endswith("_app")
    
    def get_application_features(self, app_resource: Resource) -> List[str]:
        """Get enabled features for an application resource."""
        if not self.is_application_resource(app_resource):
            return []
        
        return app_resource.get_attribute("enabled_features", [])
    
    def enable_feature(
        self,
        app_resource: Resource,
        feature: str
    ) -> Resource:
        """Enable a feature for an application resource."""
        current_features = self.get_application_features(app_resource)
        
        if feature not in current_features:
            current_features.append(feature)
            return app_resource.set_attribute("enabled_features", current_features)
        
        return app_resource
    
    def disable_feature(
        self,
        app_resource: Resource,
        feature: str
    ) -> Resource:
        """Disable a feature for an application resource."""
        current_features = self.get_application_features(app_resource)
        
        if feature in current_features:
            current_features.remove(feature)
            return app_resource.set_attribute("enabled_features", current_features)
        
        return app_resource
    
    def update_application_config(
        self,
        app_resource: Resource,
        config_updates: Dict
    ) -> Resource:
        """Update application configuration."""
        return app_resource.update_attributes(config_updates)
    
    def activate_application(self, app_resource: Resource) -> Resource:
        """Activate an application resource."""
        return app_resource.set_attribute("status", "active").activate()
    
    def deactivate_application(self, app_resource: Resource) -> Resource:
        """Deactivate an application resource."""
        return app_resource.set_attribute("status", "inactive").deactivate()
    
    def get_application_permissions(self, app_type: str) -> List[str]:
        """Get required permissions for an application type."""
        application_types = self._get_application_resource_types()
        if app_type not in application_types:
            return []
        
        return application_types[app_type]["required_permissions"]
    
    def validate_application_access(
        self,
        app_resource: Resource,
        user_permissions: List[str]
    ) -> bool:
        """Check if user has required permissions to access application."""
        required_permissions = app_resource.get_attribute("required_permissions", [])
        
        # User must have all required permissions
        return all(perm in user_permissions for perm in required_permissions)
    
    def get_available_application_types(self) -> Dict[str, Dict]:
        """Get all available application types and their metadata."""
        return self._get_application_resource_types().copy()
    
    def create_default_organization_applications(
        self,
        organization_id: UUID,
        owner_id: UUID,
        plan_type: str = "basic"
    ) -> List[Resource]:
        """
        Create default applications for a new organization based on plan.
        
        Args:
            organization_id: Organization ID
            owner_id: User who owns the applications
            plan_type: Subscription plan type
            
        Returns:
            List of created application resources
        """
        # Load plan configurations from JSON
        try:
            plan_configs = self._config_loader.load_plan_configurations()
            plan_defaults = {plan: config["applications"] for plan, config in plan_configs.items()}
            plan_features = {plan: config["features"] for plan, config in plan_configs.items()}
        except Exception:
            # Fallback to hardcoded configurations
            plan_defaults = {
                "basic": ["web_chat_app", "management_app", "document_storage"],
                "premium": ["web_chat_app", "management_app", "document_storage", "api_access"],
                "enterprise": ["web_chat_app", "management_app", "document_storage", "whatsapp_app", "api_access"]
            }
            
            plan_features = {
                "basic": [
                    "live_chat", "chat_history", "basic_customization",
                    "user_management", "organization_settings", "basic_analytics",
                    "document_upload", "document_download", "basic_search"
                ],
                "premium": [
                    "live_chat", "chat_history", "advanced_customization",
                    "user_management", "organization_settings", "advanced_analytics",
                    "document_upload", "document_download", "basic_search", "ai_query",
                    "document_sharing", "rest_api", "webhook_management"
                ],
                "enterprise": [
                    "live_chat", "chat_history", "advanced_customization", "white_label",
                    "user_management", "organization_settings", "advanced_analytics",
                    "document_upload", "document_download", "basic_search", "ai_query",
                    "document_sharing", "advanced_permissions", "ai_training",
                    "whatsapp_messaging", "template_management", "contact_sync",
                    "rest_api", "webhook_management", "advanced_integrations"
                ]
            }
        
        default_apps = plan_defaults.get(plan_type, plan_defaults["basic"])
        features = plan_features.get(plan_type, plan_features["basic"])
        
        created_apps = []
        for app_type in default_apps:
            app_resource = self.create_application_resource(
                app_type=app_type,
                organization_id=organization_id,
                owner_id=owner_id,
                plan_features=features
            )
            created_apps.append(app_resource)
        
        return created_apps

