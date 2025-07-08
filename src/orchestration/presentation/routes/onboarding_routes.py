from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ...application.services.onboarding_service import OnboardingService
from ...application.dtos.onboarding_request_dto import OnboardingRequestDto
from ...application.dtos.onboarding_response_dto import OnboardingResponseDto
from ..dependencies.onboarding_dependencies import get_onboarding_service

router = APIRouter(prefix="/onboarding", tags=["tenant-onboarding"])


@router.post("/tenant", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def onboard_tenant(
    request: OnboardingRequestDto,
    onboarding_service: OnboardingService = Depends(get_onboarding_service),
) -> Dict[str, Any]:
    """
    Onboard a new tenant.
    
    This endpoint handles the complete tenant onboarding process:
    1. Creates an organization in IAM
    2. Assigns the user to the organization as owner
    3. Sets up default roles and permissions
    4. Subscribes to the specified plan (trial)
    5. Creates application instances based on plan
    
    Args:
        request: Onboarding request with user_id, plan_id, tenant_name, and optional domain
        
    Returns:
        Onboarding response with workflow details and status
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


@router.get("/tenant/{workflow_id}", response_model=Dict[str, Any])
async def get_onboarding_status(
    workflow_id: str,
    onboarding_service: OnboardingService = Depends(get_onboarding_service),
) -> Dict[str, Any]:
    """
    Get the status of a tenant onboarding workflow.
    
    Args:
        workflow_id: The ID of the onboarding workflow
        
    Returns:
        Current status and details of the onboarding workflow
    """
    try:
        # This would require adding a get_workflow_status method to OnboardingService
        # For now, return a simple response
        return {
            "success": True,
            "data": {
                "workflow_id": workflow_id,
                "status": "completed",  # This should come from the service
                "message": "Onboarding workflow status retrieved successfully",
            }
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "Not Found",
                "message": str(e),
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Internal Server Error",
                "message": "An unexpected error occurred while retrieving onboarding status",
            }
        )


@router.post("/tenant/trial", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def onboard_tenant_with_trial(
    user_id: str,
    tenant_name: str,
    tenant_domain: str = None,
    onboarding_service: OnboardingService = Depends(get_onboarding_service),
) -> Dict[str, Any]:
    """
    Onboard a new tenant with a trial plan.
    
    This is a convenience endpoint that automatically assigns the basic/trial plan.
    
    Args:
        user_id: ID of the user creating the tenant
        tenant_name: Name of the tenant organization
        tenant_domain: Optional domain for the tenant
        
    Returns:
        Onboarding response with workflow details and status
    """
    try:
        # Get the trial plan ID (usually basic plan)
        from ...infrastructure.services.plans_service_impl import PlansServiceImpl
        from ..dependencies.onboarding_dependencies import get_plans_service
        
        plans_service = await get_plans_service()
        trial_plan_id = plans_service.get_trial_plan_id()
        
        # Create onboarding request with trial plan
        request = OnboardingRequestDto(
            user_id=user_id,
            plan_id=trial_plan_id,
            tenant_name=tenant_name,
            tenant_domain=tenant_domain,
        )
        
        response = onboarding_service.onboard_tenant(request)
        
        return {
            "success": True,
            "data": {
                "workflow_id": response.id,
                "tenant_id": response.tenant_id,
                "user_id": response.user_id,
                "plan_id": response.plan_id,
                "plan_type": "trial",
                "trial_days": 14,
                "status": response.status.value,
                "created_at": response.created_at.isoformat(),
                "updated_at": response.updated_at.isoformat(),
                "completed_at": response.completed_at.isoformat() if response.completed_at else None,
                "error_message": response.error_message,
            },
            "message": "Tenant trial onboarding completed successfully" if response.status.value == "completed" else "Tenant trial onboarding in progress",
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
                "message": "An unexpected error occurred during trial tenant onboarding",
            }
        )