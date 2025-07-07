from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ...application.services import OnboardingService
from ...application.dtos import OnboardingRequestDto, OnboardingResponseDto


router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/tenant", response_model=Dict[str, Any])
async def onboard_tenant(
    request: OnboardingRequestDto,
    onboarding_service: OnboardingService = Depends(),
) -> Dict[str, Any]:
    try:
        response = onboarding_service.onboard_tenant(request)
        
        return {
            "id": response.id,
            "tenant_id": response.tenant_id,
            "user_id": response.user_id,
            "plan_id": response.plan_id,
            "status": response.status.value,
            "created_at": response.created_at.isoformat(),
            "updated_at": response.updated_at.isoformat(),
            "completed_at": response.completed_at.isoformat() if response.completed_at else None,
            "error_message": response.error_message,
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")