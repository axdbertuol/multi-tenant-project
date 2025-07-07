from typing import Protocol
from uuid import uuid4
from datetime import datetime

from ...domain.entities import OnboardingWorkflow, OnboardingStatus
from ...domain.value_objects import TenantSetupRequest


class IamService(Protocol):
    def create_tenant(self, tenant_name: str, domain: str = None) -> str:
        ...
    
    def assign_user_to_tenant(self, user_id: str, tenant_id: str) -> None:
        ...
    
    def create_tenant_admin_role(self, tenant_id: str, user_id: str) -> None:
        ...


class PlansService(Protocol):
    def create_application_instance(self, tenant_id: str, plan_id: str) -> str:
        ...
    
    def get_plan(self, plan_id: str) -> dict:
        ...


class OnboardingRepository(Protocol):
    def save(self, workflow: OnboardingWorkflow) -> None:
        ...
    
    def get_by_id(self, workflow_id: str) -> OnboardingWorkflow:
        ...


class OnboardTenantUseCase:
    def __init__(
        self,
        iam_service: IamService,
        plans_service: PlansService,
        onboarding_repository: OnboardingRepository,
    ):
        self.iam_service = iam_service
        self.plans_service = plans_service
        self.onboarding_repository = onboarding_repository
    
    def execute(self, request: TenantSetupRequest) -> OnboardingWorkflow:
        workflow = OnboardingWorkflow(
            id=str(uuid4()),
            tenant_id="",
            user_id=request.user_id,
            plan_id=request.plan_id,
            status=OnboardingStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        try:
            workflow.start()
            self.onboarding_repository.save(workflow)
            
            # Validate plan exists
            plan = self.plans_service.get_plan(request.plan_id)
            if not plan:
                raise ValueError(f"Plan {request.plan_id} not found")
            
            # Create tenant in IAM
            tenant_id = self.iam_service.create_tenant(
                request.tenant_name, 
                request.tenant_domain
            )
            workflow.tenant_id = tenant_id
            
            # Assign user to tenant and create admin role
            self.iam_service.assign_user_to_tenant(request.user_id, tenant_id)
            self.iam_service.create_tenant_admin_role(tenant_id, request.user_id)
            
            # Create application instance in Plans
            self.plans_service.create_application_instance(tenant_id, request.plan_id)
            
            workflow.complete()
            
        except Exception as e:
            workflow.fail(str(e))
            
        finally:
            self.onboarding_repository.save(workflow)
        
        return workflow