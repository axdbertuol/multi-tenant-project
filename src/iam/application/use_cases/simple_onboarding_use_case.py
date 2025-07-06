"""Simplified user onboarding flow using resource-based applications."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from shared.domain.repositories.unit_of_work import UnitOfWork

from ...domain.entities.resource import Resource
from ...domain.entities.organization import Organization
from ...domain.repositories.resource_repository import ResourceRepository
from ...domain.services.resource_application_service import ApplicationResourceService
from ...domain.services.jwt_service import JWTService
from ..dtos.organization_dto import OrganizationCreateDTO
from .organization_use_cases import OrganizationUseCase

# Import subscription related modules
from ....plans.application.use_cases.subscription_use_cases import SubscriptionUseCase
from ....plans.application.dtos.subscription_dto import (
    SubscriptionCreateDTO,
    BillingCycleEnum,
)
from ....plans.domain.repositories.plan_repository import PlanRepository

# Import role setup service
from ...domain.services.organization_role_setup_service import (
    OrganizationRoleSetupService,
)

# Import configuration loader
from ....shared.infrastructure.config import get_configuration_loader


class SimpleOnboardingUseCase:
    """
    Simplified onboarding flow: register → subscribe → create org → setup app resources.

    This approach treats applications as resources with permissions, eliminating
    the need for complex application-specific entities and logic.
    """

    def __init__(self, organization_use_case: OrganizationUseCase, uow: UnitOfWork):
        self._uow = uow
        self._resource_repository: ResourceRepository = uow.get_repository("resource")
        self._plan_repository: PlanRepository = uow.get_repository("plan")
        self.app_service = ApplicationResourceService(self._resource_repository)
        self.jwt_service = JWTService()
        self.organization_use_case = organization_use_case
        self.subscription_use_case = SubscriptionUseCase(uow)
        self.role_setup_service = OrganizationRoleSetupService(uow)
        self._config_loader = get_configuration_loader()

    def complete_user_onboarding(
        self,
        user_id: UUID,
        organization_name: str,
        plan_type: str = "basic",
        custom_apps: Optional[List[str]] = None,
    ) -> Dict:
        """
        Complete full user onboarding: create organization + setup resource-based applications.

        Args:
            user_id: User who will own the organization
            organization_name: Name for the new organization
            plan_type: Subscription plan type
            custom_apps: Optional list of specific app types to create

        Returns:
            Dictionary with setup results
        """
        with self._uow:
            try:
                # Step 1: Create organization (tenant)
                org_dto = OrganizationCreateDTO(
                    name=organization_name,
                    description=f"Organization for {organization_name}",
                )
                organization = self.organization_use_case.create_organization(
                    org_dto, user_id
                )
                organization_id = organization.id

                # Step 2: Setup default roles and permissions for organization
                created_roles = (
                    self.role_setup_service.setup_default_roles_for_organization(
                        organization_id=organization_id, owner_user_id=user_id
                    )
                )

                # Step 3: Get or create trial plan and create subscription
                trial_plan = self._get_or_create_trial_plan(plan_type)
                subscription = self._create_trial_subscription(
                    organization_id, trial_plan.id
                )

                # Step 4: Create default application resources based on plan
                if custom_apps:
                    app_resources = []
                    for app_type in custom_apps:
                        app_resource = self.app_service.create_application_resource(
                            app_type=app_type,
                            organization_id=organization_id,
                            owner_id=user_id,
                        )
                        # Save resource to repository
                        if self._resource_repository:
                            self._resource_repository.save(app_resource)
                        app_resources.append(app_resource)
                else:
                    app_resources = (
                        self.app_service.create_default_organization_applications(
                            organization_id=organization_id,
                            owner_id=user_id,
                            plan_type=plan_type,
                        )
                    )
                    # Save all created resources to repository
                    if self._resource_repository:
                        for app_resource in app_resources:
                            self._resource_repository.save(app_resource)

                # Step 5: Generate JWT token with resource permissions
                access_token = self._generate_access_token(
                    user_id=user_id,
                    organization_id=organization_id,
                    app_resources=app_resources,
                )

                # Build response
                return {
                    "success": True,
                    "organization": {
                        "id": str(organization_id),
                        "name": organization_name,
                        "created_at": organization.created_at.isoformat(),
                    },
                    "subscription": {
                        "id": str(subscription.id),
                        "plan_id": str(subscription.plan_id),
                        "plan_name": subscription.plan_name,
                        "status": subscription.status,
                        "is_trial": subscription.is_trial,
                        "billing_cycle": subscription.billing_cycle,
                        "starts_at": subscription.starts_at.isoformat()
                        if subscription.starts_at
                        else None,
                        "ends_at": subscription.ends_at.isoformat()
                        if subscription.ends_at
                        else None,
                    },
                    "plan_type": plan_type,
                    "roles": [
                        {
                            "id": str(role.id),
                            "name": role.name.value,
                            "description": role.description,
                            "is_system_role": role.is_system_role,
                            "created_at": role.created_at.isoformat(),
                        }
                        for role in created_roles
                    ],
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
                            "required_permissions": app.get_attribute(
                                "required_permissions", []
                            ),
                        }
                        for app in app_resources
                    ],
                    "access_token": access_token,
                    "setup_completed_at": datetime.now(timezone.utc).isoformat(),
                    "next_steps": self._generate_next_steps(app_resources),
                }

            except Exception as e:
                # Transaction will be automatically rolled back by Unit of Work
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

    def _generate_access_token(
        self, user_id: UUID, organization_id: UUID, app_resources: List[Resource]
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
            roles=["organization_owner"],  # Default role for org creator
        )

    def _generate_next_steps(self, app_resources: List[Resource]) -> List[Dict]:
        """Generate recommended next steps based on created applications."""
        next_steps = []

        # Common first step
        next_steps.append(
            {
                "step": "verify_email",
                "title": "Verify Your Email",
                "description": "Check your email and click the verification link",
                "priority": "high",
                "estimated_time": "2 minutes",
            }
        )

        # Application-specific steps
        for app_resource in app_resources:
            app_type = app_resource.resource_type
            app_name = app_resource.get_attribute("app_name")

            if app_type == "web_chat_app":
                next_steps.extend(
                    [
                        {
                            "step": "configure_chat_widget",
                            "title": f"Configure {app_name}",
                            "description": "Customize your chat widget settings",
                            "priority": "medium",
                            "estimated_time": "10 minutes",
                            "resource_id": str(app_resource.id),
                        },
                        {
                            "step": "embed_chat_widget",
                            "title": "Embed Chat Widget",
                            "description": "Add the chat widget to your website",
                            "priority": "medium",
                            "estimated_time": "15 minutes",
                            "resource_id": str(app_resource.id),
                        },
                    ]
                )

            elif app_type == "management_app":
                next_steps.append(
                    {
                        "step": "invite_team_members",
                        "title": f"Setup {app_name}",
                        "description": "Invite team members and configure roles",
                        "priority": "low",
                        "estimated_time": "5 minutes",
                        "resource_id": str(app_resource.id),
                    }
                )

            elif app_type == "whatsapp_app":
                next_steps.append(
                    {
                        "step": "configure_whatsapp",
                        "title": f"Setup {app_name}",
                        "description": "Connect your WhatsApp Business account",
                        "priority": "medium",
                        "estimated_time": "20 minutes",
                        "resource_id": str(app_resource.id),
                    }
                )

            elif app_type == "document_storage":
                next_steps.extend(
                    [
                        {
                            "step": "upload_documents",
                            "title": f"Upload Your First Documents",
                            "description": "Upload documents to enable AI-powered chat responses",
                            "priority": "high",
                            "estimated_time": "10 minutes",
                            "resource_id": str(app_resource.id),
                        },
                        {
                            "step": "configure_permissions",
                            "title": "Configure Document Permissions",
                            "description": "Set up who can access and query your documents",
                            "priority": "medium",
                            "estimated_time": "5 minutes",
                            "resource_id": str(app_resource.id),
                        },
                    ]
                )

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
                "created_at": app.get_attribute("created_date"),
            }
            for app in app_resources
        ]

    def enable_application_feature(
        self, organization_id: UUID, app_resource_id: UUID, feature: str
    ) -> bool:
        """Enable a feature for an application resource."""
        try:
            app_resource = self._resource_repository.find_by_id(app_resource_id)
            if not app_resource or app_resource.organization_id != organization_id:
                return False

            updated_resource = self.app_service.enable_feature(app_resource, feature)
            self._resource_repository.update(updated_resource)
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
        user_permissions: List[str],
    ) -> bool:
        """
        Validate if user can access an application resource.

        This leverages the existing RBAC/ABAC system by checking if the user
        has the required permissions for the application resource.
        """
        try:
            app_resource = self._resource_repository.get_by_id(app_resource_id)
            if not app_resource or app_resource.organization_id != organization_id:
                return False

            return self.app_service.validate_application_access(
                app_resource, user_permissions
            )
        except Exception:
            return False

    def create_custom_application(
        self,
        organization_id: UUID,
        owner_id: UUID,
        app_type: str,
        custom_config: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """Create a custom application resource."""
        try:
            app_resource = self.app_service.create_application_resource(
                app_type=app_type,
                organization_id=organization_id,
                owner_id=owner_id,
                custom_config=custom_config,
            )

            self._resource_repository.save(app_resource)

            return {
                "id": str(app_resource.id),
                "type": app_resource.resource_type,
                "name": app_resource.get_attribute("app_name"),
                "status": app_resource.get_attribute("status"),
                "features": app_resource.get_attribute("enabled_features", []),
                "created_at": app_resource.get_attribute("created_date"),
            }
        except Exception:
            return None

    def _get_or_create_trial_plan(self, plan_type: str):
        """Get or create a trial plan for the specified plan type."""
        # First try to find existing trial plan
        plans = self._plan_repository.get_by_type(plan_type)
        trial_plan = None

        for plan in plans:
            if plan.is_active and plan.status.value == "active":
                trial_plan = plan
                break

        if not trial_plan:
            # If no plan found, return the first available plan of the type
            # In production, you might want to create a default trial plan here
            if plans:
                trial_plan = plans[0]
            else:
                raise ValueError(f"No plan found for type: {plan_type}")

        return trial_plan

    def _create_trial_subscription(self, organization_id: UUID, plan_id: UUID):
        """Create a trial subscription for the organization."""
        # Load trial settings from configuration
        try:
            trial_settings = self._config_loader.load_trial_settings()
            trial_config = trial_settings.get("trial_config", {})
            
            billing_cycle = trial_config.get("billing_cycle", "monthly")
            duration_days = trial_config.get("duration_days", 30)
            metadata = trial_config.get("metadata", {
                "is_trial": True,
                "created_via": "onboarding"
            })
            metadata["trial_duration_days"] = duration_days
            
        except Exception:
            # Fallback to hardcoded values
            billing_cycle = "monthly"
            metadata = {
                "is_trial": True,
                "trial_duration_days": 30,
                "created_via": "onboarding",
            }
        
        subscription_dto = SubscriptionCreateDTO(
            organization_id=organization_id,
            plan_id=plan_id,
            billing_cycle=BillingCycleEnum.MONTHLY if billing_cycle == "monthly" else BillingCycleEnum.YEARLY,
            starts_at=datetime.now(timezone.utc),
            metadata=metadata,
        )

        return self.subscription_use_case.create_subscription(subscription_dto)
