from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from ...domain.entities import OnboardingStatus


@dataclass
class OnboardingResponseDto:
    id: str
    tenant_id: str
    user_id: str
    plan_id: str
    status: OnboardingStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None