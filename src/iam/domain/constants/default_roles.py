"""Default organization roles and their configurations."""

from enum import Enum
from typing import Dict, List


class DefaultOrganizationRoles(Enum):
    """Default roles created for new organizations."""
    
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class DefaultRoleConfigurations:
    """Default configurations for organization roles."""
    
    ROLE_CONFIGS: Dict[str, Dict[str, any]] = {
        DefaultOrganizationRoles.OWNER.value: {
            "description": "Organization owner with full access",
            "permissions": [
                "organization:*",
                "user:*",
                "role:*",
                "permission:*",
                "resource:*",
                "application:*",
                "document:*"
            ],
            "is_system_role": True,
            "can_be_deleted": False,
        },
        DefaultOrganizationRoles.ADMIN.value: {
            "description": "Organization administrator with management access",
            "permissions": [
                "organization:read",
                "organization:update",
                "user:*",
                "role:*",
                "permission:read",
                "resource:*",
                "application:*",
                "document:read",
                "document:create",
                "document:update",
                "document:delete",
                "document:share",
                "document:manage",
                "document:ai_query",
                "document:train"
            ],
            "is_system_role": True,
            "can_be_deleted": False,
        },
        DefaultOrganizationRoles.MEMBER.value: {
            "description": "Organization member with standard access",
            "permissions": [
                "organization:read",
                "user:read",
                "role:read",
                "resource:read",
                "resource:use",
                "application:read",
                "application:use",
                "document:read",
                "document:create",
                "document:update",
                "document:share",
                "document:download",
                "document:ai_query"
            ],
            "is_system_role": True,
            "can_be_deleted": False,
        },
        DefaultOrganizationRoles.VIEWER.value: {
            "description": "Organization viewer with read-only access",
            "permissions": [
                "organization:read",
                "user:read",
                "role:read",
                "resource:read",
                "application:read",
                "document:read",
                "document:download"
            ],
            "is_system_role": True,
            "can_be_deleted": False,
        },
    }
    
    @classmethod
    def get_role_config(cls, role_name: str) -> Dict[str, any]:
        """Get configuration for a specific role."""
        return cls.ROLE_CONFIGS.get(role_name, {})
    
    @classmethod
    def get_default_permissions(cls, role_name: str) -> List[str]:
        """Get default permissions for a role."""
        config = cls.get_role_config(role_name)
        return config.get("permissions", [])
    
    @classmethod
    def get_all_default_roles(cls) -> List[str]:
        """Get all default role names."""
        return list(cls.ROLE_CONFIGS.keys())