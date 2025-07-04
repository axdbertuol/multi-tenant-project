"""Simplified user onboarding flow using resource-based applications."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ...domain.entities.resource import Resource
from ...domain.services.resource_application_service import ApplicationResourceService
from ...domain.services.jwt_service import JWTService


class SimpleOnboardingUseCase:
    """
    Simplified onboarding flow: register → subscribe → create org → setup app resources.
    
    This approach treats applications as resources with permissions, eliminating
    the need for complex application-specific entities and logic.
    """
    
    def __init__(self):
        self.app_service = ApplicationResourceService()
        self.jwt_service = JWTService()
    
    def complete_organization_setup(
        self,
        user_id: UUID,
        organization_id: UUID,
        organization_name: str,
        plan_type: str = "basic",
        custom_apps: Optional[List[str]] = None
    ) -> Dict:
        """
        Complete organization setup with resource-based applications.
        
        Args:
            user_id: User who owns the organization
            organization_id: Organization ID (already created)
            organization_name: Organization name
            plan_type: Subscription plan type
            custom_apps: Optional list of specific app types to create
            
        Returns:
            Dictionary with setup results
        """
        try:
            # Create default application resources based on plan
            if custom_apps:
                app_resources = []
                for app_type in custom_apps:
                    app_resource = self.app_service.create_application_resource(
                        app_type=app_type,
                        organization_id=organization_id,
                        owner_id=user_id
                    )
                    app_resources.append(app_resource)
            else:
                app_resources = self.app_service.create_default_organization_applications(
                    organization_id=organization_id,
                    owner_id=user_id,
                    plan_type=plan_type
                )
            
            # Generate JWT token with resource permissions
            access_token = self._generate_access_token(
                user_id=user_id,
                organization_id=organization_id,
                app_resources=app_resources
            )
            
            # Build response
            return {
                "success": True,
                "organization_id": str(organization_id),
                "organization_name": organization_name,
                "plan_type": plan_type,
                "applications": [
                    {
                        "id": str(app.id),
                        "type": app.resource_type,
                        "name": app.get_attribute("app_name"),
                        "description": app.get_attribute("app_description"),
                        "icon": app.get_attribute("app_icon"),
                        "category": app.get_attribute("app_category"),
                        "status": app.get_attribute("status"),
                        "features": app.get_attribute("enabled_features", []),
                        "required_permissions": app.get_attribute("required_permissions", [])
                    }
                    for app in app_resources
                ],
                "access_token": access_token,
                "setup_completed_at": datetime.now(timezone.utc).isoformat(),
                "next_steps": self._generate_next_steps(app_resources)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _generate_access_token(
        self,
        user_id: UUID,
        organization_id: UUID,
        app_resources: List[Resource]
    ) -> str:
        """Generate JWT token with resource permissions."""
        
        # Collect all required permissions from application resources
        all_permissions = []
        for app_resource in app_resources:
            required_perms = app_resource.get_attribute("required_permissions", [])
            all_permissions.extend(required_perms)
        
        # Remove duplicates
        unique_permissions = list(set(all_permissions))
        
        # For now, assume user has all required permissions
        # In real implementation, this would check user's actual permissions
        user_permissions = unique_permissions
        
        # Generate JWT token
        return self.jwt_service.create_access_token(
            user_id=str(user_id),
            organization_id=str(organization_id),
            permissions=user_permissions,
            roles=["organization_owner"]  # Default role for org creator
        )
    
    def _generate_next_steps(self, app_resources: List[Resource]) -> List[Dict]:
        """Generate recommended next steps based on created applications."""
        next_steps = []
        
        # Common first step
        next_steps.append({
            "step": "verify_email",
            "title": "Verify Your Email",
            "description": "Check your email and click the verification link",
            "priority": "high",
            "estimated_time": "2 minutes"
        })
        
        # Application-specific steps
        for app_resource in app_resources:
            app_type = app_resource.resource_type
            app_name = app_resource.get_attribute("app_name")
            
            if app_type == "web_chat_app":
                next_steps.extend([
                    {
                        "step": "configure_chat_widget",
                        "title": f"Configure {app_name}",
                        "description": "Customize your chat widget settings",
                        "priority": "medium",
                        "estimated_time": "10 minutes",
                        "resource_id": str(app_resource.id)
                    },
                    {
                        "step": "embed_chat_widget",
                        "title": "Embed Chat Widget",
                        "description": "Add the chat widget to your website",
                        "priority": "medium", 
                        "estimated_time": "15 minutes",
                        "resource_id": str(app_resource.id)
                    }
                ])
            
            elif app_type == "management_app":
                next_steps.append({
                    "step": "invite_team_members",
                    "title": f"Setup {app_name}",
                    "description": "Invite team members and configure roles",
                    "priority": "low",
                    "estimated_time": "5 minutes",
                    "resource_id": str(app_resource.id)
                })
            
            elif app_type == "whatsapp_app":
                next_steps.append({
                    "step": "configure_whatsapp",
                    "title": f"Setup {app_name}",
                    "description": "Connect your WhatsApp Business account",
                    "priority": "medium",
                    "estimated_time": "20 minutes",
                    "resource_id": str(app_resource.id)
                })
        
        return next_steps
    
    def get_organization_applications(self, organization_id: UUID) -> List[Dict]:
        """Get all application resources for an organization."""
        app_resources = self.app_service.get_organization_applications(organization_id)
        
        return [
            {
                "id": str(app.id),
                "type": app.resource_type,
                "name": app.get_attribute("app_name"),
                "description": app.get_attribute("app_description"),
                "status": app.get_attribute("status"),
                "features": app.get_attribute("enabled_features", []),
                "created_at": app.get_attribute("created_date")
            }
            for app in app_resources
        ]
    
    def enable_application_feature(
        self,
        organization_id: UUID,
        app_resource_id: UUID,
        feature: str
    ) -> bool:
        """Enable a feature for an application resource."""
        try:
            # TODO: Implement with actual repository
            # app_resource = resource_repository.find_by_id(app_resource_id)
            # if not app_resource or app_resource.organization_id != organization_id:
            #     return False
            # 
            # updated_resource = self.app_service.enable_feature(app_resource, feature)
            # resource_repository.update(updated_resource)
            # return True
            return True
        except Exception:
            return False
    
    def get_available_applications(self) -> Dict[str, Dict]:
        """Get all available application types."""
        return self.app_service.get_available_application_types()
    
    def validate_user_application_access(
        self,
        user_id: UUID,
        organization_id: UUID,
        app_resource_id: UUID,
        user_permissions: List[str]
    ) -> bool:
        """
        Validate if user can access an application resource.
        
        This leverages the existing RBAC/ABAC system by checking if the user
        has the required permissions for the application resource.
        """
        try:
            # TODO: Implement with actual repository
            # app_resource = resource_repository.find_by_id(app_resource_id)
            # if not app_resource or app_resource.organization_id != organization_id:
            #     return False
            # 
            # return self.app_service.validate_application_access(
            #     app_resource, user_permissions
            # )
            return True
        except Exception:
            return False
    
    def create_custom_application(
        self,
        organization_id: UUID,
        owner_id: UUID,
        app_type: str,
        custom_config: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Create a custom application resource."""
        try:
            app_resource = self.app_service.create_application_resource(
                app_type=app_type,
                organization_id=organization_id,
                owner_id=owner_id,
                custom_config=custom_config
            )
            
            # TODO: Save to repository
            # resource_repository.save(app_resource)
            
            return {
                "id": str(app_resource.id),
                "type": app_resource.resource_type,
                "name": app_resource.get_attribute("app_name"),
                "status": app_resource.get_attribute("status"),
                "features": app_resource.get_attribute("enabled_features", []),
                "created_at": app_resource.get_attribute("created_date")
            }
        except Exception as e:
            return None