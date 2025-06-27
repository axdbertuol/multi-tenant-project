from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import BaseModel


class UserOrganizationRole(BaseModel):
    id: UUID
    user_id: UUID
    organization_id: UUID
    role_id: UUID
    assigned_at: datetime
    assigned_by: UUID
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None
    is_active: bool = True

    model_config = {"frozen": True}

    @classmethod
    def create(cls, user_id: UUID, organization_id: UUID, role_id: UUID, assigned_by: UUID) -> "UserOrganizationRole":
        return cls(
            id=uuid4(),
            user_id=user_id,
            organization_id=organization_id,
            role_id=role_id,
            assigned_by=assigned_by,
            assigned_at=datetime.utcnow(),
            is_active=True
        )

    def revoke(self, revoked_by: UUID) -> "UserOrganizationRole":
        return self.model_copy(update={
            "revoked_at": datetime.utcnow(),
            "revoked_by": revoked_by,
            "is_active": False
        })

    def reactivate(self) -> "UserOrganizationRole":
        return self.model_copy(update={
            "revoked_at": None,
            "revoked_by": None,
            "is_active": True
        })