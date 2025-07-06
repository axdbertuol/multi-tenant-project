from datetime import datetime, timezone

from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel
from enum import Enum

from ..value_objects.permission_name import PermissionName


class PermissionAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"
    # Document-specific actions
    SHARE = "share"          # Share document with others
    DOWNLOAD = "download"    # Download document file
    AI_QUERY = "ai_query"    # Allow AI to reference in responses
    AI_CITE = "ai_cite"      # Allow AI to cite this document
    TRAIN = "train"          # Include in AI training


class Permission(BaseModel):
    id: UUID
    name: PermissionName
    description: str
    action: PermissionAction
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
        action: PermissionAction,
        resource_type: str,
        is_system_permission: bool = False,
    ) -> "Permission":
        return cls(
            id=uuid4(),
            name=PermissionName(value=name),
            description=description,
            action=action,
            resource_type=resource_type,
            created_at=datetime.now(timezone.utc),
            is_active=True,
            is_system_permission=is_system_permission,
        )

    def update_description(self, description: str) -> "Permission":
        return self.model_copy(
            update={"description": description, "updated_at": datetime.utcnow()}
        )

    def deactivate(self) -> "Permission":
        if self.is_system_permission:
            raise ValueError("Cannot deactivate system permissions")

        return self.model_copy(
            update={"is_active": False, "updated_at": datetime.utcnow()}
        )

    def activate(self) -> "Permission":
        return self.model_copy(
            update={"is_active": True, "updated_at": datetime.now(timezone.utc)}
        )

    def get_full_name(self) -> str:
        """Get full permission name in format: resource_type:action"""
        return f"{self.resource_type}:{self.action.value}"

    def can_be_deleted(self) -> tuple[bool, str]:
        """Check if permission can be deleted."""
        if self.is_system_permission:
            return False, "System permissions cannot be deleted"

        return True, "Permission can be deleted"

    def matches_resource_and_action(
        self, resource_type: str, action: PermissionAction
    ) -> bool:
        """Check if this permission matches the given resource and action."""
        return (
            self.resource_type == resource_type
            and self.action == action
            and self.is_active
        )
