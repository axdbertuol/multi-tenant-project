from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class OnboardingStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class OnboardingWorkflow:
    id: str
    tenant_id: str
    user_id: str
    plan_id: str
    status: OnboardingStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def start(self) -> None:
        self.status = OnboardingStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
    
    def complete(self) -> None:
        self.status = OnboardingStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def fail(self, error_message: str) -> None:
        self.status = OnboardingStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def is_completed(self) -> bool:
        return self.status == OnboardingStatus.COMPLETED
    
    def is_failed(self) -> bool:
        return self.status == OnboardingStatus.FAILED