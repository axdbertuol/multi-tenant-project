from sqlalchemy.orm import Session
from sqlalchemy import select

from ...domain.entities import OnboardingWorkflow
from ..database.models import OnboardingWorkflowModel


class SqlAlchemyOnboardingRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, workflow: OnboardingWorkflow) -> None:
        existing = self.session.get(OnboardingWorkflowModel, workflow.id)
        
        if existing:
            existing.tenant_id = workflow.tenant_id
            existing.status = workflow.status.value
            existing.updated_at = workflow.updated_at
            existing.completed_at = workflow.completed_at
            existing.error_message = workflow.error_message
        else:
            model = OnboardingWorkflowModel(
                id=workflow.id,
                tenant_id=workflow.tenant_id,
                user_id=workflow.user_id,
                plan_id=workflow.plan_id,
                status=workflow.status.value,
                created_at=workflow.created_at,
                updated_at=workflow.updated_at,
                completed_at=workflow.completed_at,
                error_message=workflow.error_message,
            )
            self.session.add(model)
        
        self.session.commit()
    
    def get_by_id(self, workflow_id: str) -> OnboardingWorkflow:
        model = self.session.get(OnboardingWorkflowModel, workflow_id)
        if not model:
            raise ValueError(f"Onboarding workflow {workflow_id} not found")
        
        return OnboardingWorkflow(
            id=model.id,
            tenant_id=model.tenant_id,
            user_id=model.user_id,
            plan_id=model.plan_id,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at,
            error_message=model.error_message,
        )