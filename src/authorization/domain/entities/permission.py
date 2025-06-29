from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel
from enum import Enum

from ..value_objects.permission_name import PermissionName


class PermissionType(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"


class Permission(BaseModel):
    id: UUID
    name: PermissionName
    description: str
    permission_type: PermissionType
    resource_type: str  # e.g., "user", "organization", "chat"
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    is_system_permission: bool = False

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    @classmethod
    def create(
        cls, 
        name: str, 
        description: str, 
        permission_type: PermissionType,
        resource_type: str,
        is_system_permission: bool = False
    ) -> "Permission":
        return cls(
            id=uuid4(),
            name=PermissionName(value=name),
            description=description,
            permission_type=permission_type,
            resource_type=resource_type,
            created_at=datetime.utcnow(),
            is_active=True,
            is_system_permission=is_system_permission
        )

    def update_description(self, description: str) -> "Permission":
        return self.model_copy(update={
            "description": description,
            "updated_at": datetime.utcnow()
        })

    def deactivate(self) -> "Permission":
        if self.is_system_permission:
            raise ValueError("Cannot deactivate system permissions")
        
        return self.model_copy(update={
            "is_active": False,
            "updated_at": datetime.utcnow()
        })

    def activate(self) -> "Permission":
        return self.model_copy(update={
            "is_active": True,
            "updated_at": datetime.utcnow()
        })

    def get_full_name(self) -> str:
        """Get full permission name in format: resource_type:permission_type"""
        return f"{self.resource_type}:{self.permission_type.value}"

    def can_be_deleted(self) -> tuple[bool, str]:
        """Check if permission can be deleted."""
        if self.is_system_permission:
            return False, "System permissions cannot be deleted"
        
        return True, "Permission can be deleted"

    def matches_resource_and_action(self, resource_type: str, action: PermissionType) -> bool:
        """Check if this permission matches the given resource and action."""
        return (
            self.resource_type == resource_type and 
            self.permission_type == action and 
            self.is_active
        )