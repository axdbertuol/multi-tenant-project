from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ...application.services.onboarding_service import OnboardingService
from ...application.dtos.onboarding_request_dto import OnboardingRequestDto
from ..dependencies.onboarding_dependencies import get_onboarding_service


router = APIRouter(prefix="/onboarding", tags=["tenant-onboarding"])


@router.post("/tenant", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def onboard_tenant(
    request: OnboardingRequestDto,
    onboarding_service: OnboardingService = Depends(get_onboarding_service),
) -> Dict[str, Any]:
    """
    Onboard a new tenant with complete setup.
    
    This endpoint handles the complete tenant onboarding process:
    1. Creates an organization in IAM
    2. Assigns the user to the organization as owner
    3. Sets up default roles and permissions  
    4. Subscribes to the specified plan
    5. Creates application instances based on plan
    """
    try:
        response = onboarding_service.onboard_tenant(request)
        
        return {
            "success": True,
            "data": {
                "workflow_id": response.id,
                "tenant_id": response.tenant_id,
                "user_id": response.user_id,
                "plan_id": response.plan_id,
                "status": response.status.value,
                "created_at": response.created_at.isoformat(),
                "updated_at": response.updated_at.isoformat(),
                "completed_at": response.completed_at.isoformat() if response.completed_at else None,
                "error_message": response.error_message,
            },
            "message": "Tenant onboarding completed successfully" if response.status.value == "completed" else "Tenant onboarding in progress",
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "Validation Error",
                "message": str(e),
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Internal Server Error", 
                "message": "An unexpected error occurred during tenant onboarding",
            }
        )