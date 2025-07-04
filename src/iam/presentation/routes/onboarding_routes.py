"""User onboarding routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from ..dependencies import get_organization_use_case
from ...application.use_cases.organization_use_cases import OrganizationUseCase
from ...application.use_cases.simple_onboarding_use_case import SimpleOnboardingUseCase

router = APIRouter(prefix="/onboarding", tags=["User Onboarding"])


class OnboardingRequestDTO(BaseModel):
    """DTO for user onboarding request."""
    user_id: UUID
    organization_name: str
    plan_type: str = "basic"
    custom_apps: Optional[List[str]] = None


@router.post("/complete")
def complete_user_onboarding(
    dto: OnboardingRequestDTO,
    organization_use_case: OrganizationUseCase = Depends(get_organization_use_case),
):
    """
    Complete full user onboarding flow.
    
    This endpoint:
    1. Creates a new organization (tenant) for the user
    2. Sets up default application resources based on plan
    3. Generates JWT token with appropriate permissions
    4. Returns complete onboarding results
    
    This integrates the simplified resource-based application approach
    where applications are just special resource types.
    """
    try:
        # Initialize onboarding service with organization use case
        onboarding_service = SimpleOnboardingUseCase(organization_use_case)
        
        # Complete the onboarding process
        result = onboarding_service.complete_user_onboarding(
            user_id=dto.user_id,
            organization_name=dto.organization_name,
            plan_type=dto.plan_type,
            custom_apps=dto.custom_apps
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Onboarding failed: {str(e)}"
        )


@router.get("/available-apps")
def get_available_applications():
    """Get available application types for onboarding."""
    from ...domain.services.resource_application_service import ApplicationResourceService
    
    app_service = ApplicationResourceService()
    return {
        "available_applications": app_service.get_available_application_types(),
        "recommended_by_plan": {
            "basic": ["web_chat_app", "management_app"],
            "premium": ["web_chat_app", "management_app", "api_access"],
            "enterprise": ["web_chat_app", "management_app", "whatsapp_app", "api_access"]
        }
    }


@router.get("/status/{user_id}")
def get_onboarding_status(
    user_id: UUID,
    organization_use_case: OrganizationUseCase = Depends(get_organization_use_case),
):
    """Get onboarding status for a user."""
    try:
        # Check if user has any organizations
        organizations = organization_use_case.list_organizations(
            page=1,
            page_size=10,
            owner_id=user_id,
            active_only=True
        )
        
        has_organization = len(organizations.items) > 0
        
        if has_organization:
            # Get applications for the first organization
            onboarding_service = SimpleOnboardingUseCase(organization_use_case)
            org_id = organizations.items[0].id
            applications = onboarding_service.get_organization_applications(org_id)
            
            return {
                "onboarding_completed": True,
                "organization": organizations.items[0],
                "applications": applications,
                "total_organizations": len(organizations.items)
            }
        else:
            return {
                "onboarding_completed": False,
                "organization": None,
                "applications": [],
                "total_organizations": 0,
                "next_step": "Create organization and select applications"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get onboarding status: {str(e)}"
        )