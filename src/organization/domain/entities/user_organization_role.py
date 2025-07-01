from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel
from enum import Enum

# TODO: Remove this enum - kept for backwards compatibility during migration
# Services should be updated to use role_id foreign keys instead
class OrganizationRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class UserOrganizationRole(BaseModel):
    """
    Domain entity representing a user's role assignment within an organization.
    
    This entity uses foreign key references to authorization.Role entities,
    providing flexibility for dynamic role management.
    """
    id: UUID
    user_id: UUID
    organization_id: UUID
    role_id: UUID  # Foreign key to authorization.Role
    assigned_by: UUID
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        user_id: UUID,
        organization_id: UUID,
        role_id: UUID,
        assigned_by: UUID,
        expires_at: Optional[datetime] = None
    ) -> "UserOrganizationRole":
        """
        Create a new user organization role assignment.
        
        Args:
            user_id: UUID of the user being assigned the role
            organization_id: UUID of the organization
            role_id: UUID of the role (foreign key to authorization.Role)
            assigned_by: UUID of the user making the assignment
            expires_at: Optional expiration date for the role assignment
        """
        return cls(
            id=uuid4(),
            user_id=user_id,
            organization_id=organization_id,
            role_id=role_id,
            assigned_by=assigned_by,
            assigned_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_active=True,
            revoked_at=None,
            revoked_by=None
        )

    def change_role(self, new_role_id: UUID, changed_by: UUID) -> "UserOrganizationRole":
        """
        Change user role in organization.
        
        Args:
            new_role_id: UUID of the new role (foreign key to authorization.Role)
            changed_by: UUID of the user making the change
        """
        return self.model_copy(update={
            "role_id": new_role_id,
            "assigned_by": changed_by,
            "assigned_at": datetime.now(timezone.utc)
        })

    def deactivate(self) -> "UserOrganizationRole":
        """Deactivate user role in organization."""
        return self.model_copy(update={"is_active": False})

    def activate(self) -> "UserOrganizationRole":
        """Activate user role in organization."""
        return self.model_copy(update={"is_active": True})
    
    def revoke(self, revoked_by: UUID) -> "UserOrganizationRole":
        """Revoke user role in organization."""
        return self.model_copy(update={
            "is_active": False,
            "revoked_at": datetime.now(timezone.utc),
            "revoked_by": revoked_by
        })
    
    def reactivate(self) -> "UserOrganizationRole":
        """Reactivate a revoked user role."""
        return self.model_copy(update={
            "is_active": True,
            "revoked_at": None,
            "revoked_by": None
        })

    def is_expired(self) -> bool:
        """Check if role assignment has expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """
        Check if role assignment is valid (active and not expired).
        
        Note: Role-specific permissions should be checked through the 
        authorization domain services using the role_id.
        """
        return self.is_active and not self.is_expired()