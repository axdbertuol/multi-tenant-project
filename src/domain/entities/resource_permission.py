from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class PermissionEffect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class ContextCondition(BaseModel):
    """Defines conditions that must be met for the permission to apply"""
    attribute: str  # e.g., "user.department", "resource.project_code", "context.time"
    operator: str  # e.g., "equals", "in", "contains", "greater_than"
    value: Any  # e.g., "engineering", ["proj_a", "proj_b"], "2024-01-01"

    model_config = {"frozen": True}


class ResourcePermission(BaseModel):
    """Specific permission for a user/role on a resource with contextual conditions"""
    id: UUID
    user_id: Optional[UUID] = None  # Direct user permission
    role_id: Optional[UUID] = None  # Role-based permission
    resource_id: UUID
    permission_id: UUID  # Links to base Permission (read, write, delete, etc.)
    effect: PermissionEffect = PermissionEffect.ALLOW
    conditions: list[ContextCondition] = []  # ABAC conditions
    priority: int = 0  # Higher priority rules override lower ones
    assigned_at: datetime
    assigned_by: UUID
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None
    is_active: bool = True

    model_config = {"frozen": True}

    @classmethod
    def create_user_permission(
        cls,
        user_id: UUID,
        resource_id: UUID,
        permission_id: UUID,
        assigned_by: UUID,
        effect: PermissionEffect = PermissionEffect.ALLOW,
        conditions: Optional[list[ContextCondition]] = None,
        priority: int = 0,
    ) -> "ResourcePermission":
        return cls(
            id=uuid4(),
            user_id=user_id,
            resource_id=resource_id,
            permission_id=permission_id,
            effect=effect,
            conditions=conditions or [],
            priority=priority,
            assigned_at=datetime.utcnow(),
            assigned_by=assigned_by,
            is_active=True,
        )

    @classmethod
    def create_role_permission(
        cls,
        role_id: UUID,
        resource_id: UUID,
        permission_id: UUID,
        assigned_by: UUID,
        effect: PermissionEffect = PermissionEffect.ALLOW,
        conditions: Optional[list[ContextCondition]] = None,
        priority: int = 0,
    ) -> "ResourcePermission":
        return cls(
            id=uuid4(),
            role_id=role_id,
            resource_id=resource_id,
            permission_id=permission_id,
            effect=effect,
            conditions=conditions or [],
            priority=priority,
            assigned_at=datetime.utcnow(),
            assigned_by=assigned_by,
            is_active=True,
        )

    def revoke(self, revoked_by: UUID) -> "ResourcePermission":
        return self.model_copy(update={
            "revoked_at": datetime.utcnow(),
            "revoked_by": revoked_by,
            "is_active": False,
        })

    def update_conditions(self, conditions: list[ContextCondition]) -> "ResourcePermission":
        return self.model_copy(update={"conditions": conditions})

    def update_priority(self, priority: int) -> "ResourcePermission":
        return self.model_copy(update={"priority": priority})