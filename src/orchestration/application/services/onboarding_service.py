from ..use_cases import OnboardTenantUseCase
from ..dtos import OnboardingRequestDto, OnboardingResponseDto
from ...domain.value_objects import TenantSetupRequest


class OnboardingService:
    def __init__(self, onboard_tenant_use_case: OnboardTenantUseCase):
        self.onboard_tenant_use_case = onboard_tenant_use_case
    
    def onboard_tenant(self, request: OnboardingRequestDto) -> OnboardingResponseDto:
        setup_request = TenantSetupRequest(
            user_id=request.user_id,
            plan_id=request.plan_id,
            tenant_name=request.tenant_name,
            tenant_domain=request.tenant_domain,
        )
        
        workflow = self.onboard_tenant_use_case.execute(setup_request)
        
        return OnboardingResponseDto(
            id=workflow.id,
            tenant_id=workflow.tenant_id,
            user_id=workflow.user_id,
            plan_id=workflow.plan_id,
            status=workflow.status,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            completed_at=workflow.completed_at,
            error_message=workflow.error_message,
        )