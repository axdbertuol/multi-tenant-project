from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TenantSetupRequest:
    user_id: str
    plan_id: str
    tenant_name: str
    tenant_domain: Optional[str] = None
    
    def __post_init__(self):
        if not self.user_id:
            raise ValueError("User ID is required")
        if not self.plan_id:
            raise ValueError("Plan ID is required")
        if not self.tenant_name:
            raise ValueError("Tenant name is required")
        if len(self.tenant_name) < 3:
            raise ValueError("Tenant name must be at least 3 characters")
        if self.tenant_domain and len(self.tenant_domain) < 3:
            raise ValueError("Tenant domain must be at least 3 characters")