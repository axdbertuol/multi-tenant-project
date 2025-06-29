from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class OrganizationRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class UserOrganizationRole(BaseModel):
    id: UUID
    user_id: UUID
    organization_id: UUID
    role: OrganizationRole
    assigned_by: UUID
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        user_id: UUID,
        organization_id: UUID,
        role: OrganizationRole,
        assigned_by: UUID,
        expires_at: Optional[datetime] = None
    ) -> "UserOrganizationRole":
        return cls(
            id=uuid4(),
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            assigned_by=assigned_by,
            assigned_at=datetime.utcnow(),
            expires_at=expires_at,
            is_active=True
        )

    def change_role(self, new_role: OrganizationRole, changed_by: UUID) -> "UserOrganizationRole":
        """Change user role in organization."""
        return self.model_copy(update={
            "role": new_role,
            "assigned_by": changed_by,
            "assigned_at": datetime.utcnow()
        })

    def deactivate(self) -> "UserOrganizationRole":
        """Deactivate user role in organization."""
        return self.model_copy(update={"is_active": False})

    def activate(self) -> "UserOrganizationRole":
        """Activate user role in organization."""
        return self.model_copy(update={"is_active": True})

    def is_expired(self) -> bool:
        """Check if role assignment has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if role assignment is valid (active and not expired)."""
        return self.is_active and not self.is_expired()

    def has_admin_privileges(self) -> bool:
        """Check if role has admin privileges."""
        return self.role in [OrganizationRole.OWNER, OrganizationRole.ADMIN]

    def can_manage_users(self) -> bool:
        """Check if role can manage other users."""
        return self.role in [OrganizationRole.OWNER, OrganizationRole.ADMIN]

    def can_modify_organization(self) -> bool:
        """Check if role can modify organization settings."""
        return self.role == OrganizationRole.OWNER