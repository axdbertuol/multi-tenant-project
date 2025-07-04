"""Service for managing applications as resources."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..entities.resource import Resource
from ...application.dtos.resource_dto import ResourceCreateDTO


class ApplicationResourceService:
    """
    Service for managing applications as special resource types.
    
    This approach treats applications as resources with specific attributes,
    leveraging the existing RBAC/ABAC system for permissions.
    """
    
    # Standard application resource types
    APPLICATION_RESOURCE_TYPES = {
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
        if app_type not in self.APPLICATION_RESOURCE_TYPES:
            raise ValueError(f"Unknown application type: {app_type}")
        
        app_config = self.APPLICATION_RESOURCE_TYPES[app_type]
        
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
        
        # Add custom configuration
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
        
        This would typically query the resource repository.
        """
        # TODO: Implement with actual repository
        # return resource_repository.find_by_organization_and_type_pattern(
        #     organization_id, "*_app"
        # )
        return []
    
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
        if app_type not in self.APPLICATION_RESOURCE_TYPES:
            return []
        
        return self.APPLICATION_RESOURCE_TYPES[app_type]["required_permissions"]
    
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
        return self.APPLICATION_RESOURCE_TYPES.copy()
    
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
        # Define plan-based default apps
        plan_defaults = {
            "basic": ["web_chat_app", "management_app"],
            "premium": ["web_chat_app", "management_app", "api_access"],
            "enterprise": ["web_chat_app", "management_app", "whatsapp_app", "api_access"]
        }
        
        # Define plan-based features
        plan_features = {
            "basic": [
                "live_chat", "chat_history", "basic_customization",
                "user_management", "organization_settings", "basic_analytics"
            ],
            "premium": [
                "live_chat", "chat_history", "advanced_customization",
                "user_management", "organization_settings", "advanced_analytics",
                "rest_api", "webhook_management"
            ],
            "enterprise": [
                "live_chat", "chat_history", "advanced_customization", "white_label",
                "user_management", "organization_settings", "advanced_analytics",
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