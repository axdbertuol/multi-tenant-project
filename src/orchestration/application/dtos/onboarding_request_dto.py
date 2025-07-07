from dataclasses import dataclass
from typing import Optional


@dataclass
class OnboardingRequestDto:
    user_id: str
    plan_id: str
    tenant_name: str
    tenant_domain: Optional[str] = None