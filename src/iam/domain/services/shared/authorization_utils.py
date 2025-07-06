"""Shared authorization utilities for IAM services."""

from typing import List, Optional, Set
from uuid import UUID

from ...entities.authorization_context import AuthorizationContext
from ...entities.permission import Permission
from ...entities.role import Role


class AuthorizationUtils:
    """Utility class for common authorization patterns."""

    @staticmethod
    def check_permission_match(
        required_permission: str, user_permissions: List[str]
    ) -> bool:
        """
        Check if user has required permission including wildcard matches.
        
        Used in: RBACService, JWTService, AuthorizationService
        """
        # Check exact match
        if required_permission in user_permissions:
            return True

        # Parse required permission
        if ":" not in required_permission:
            return False

        resource_type, action = required_permission.split(":", 1)

        # Check wildcard permissions
        wildcards_to_check = [
            f"{resource_type}:*",  # Resource wildcard
            f"*:{action}",  # Action wildcard
            "*:*",  # Global wildcard
        ]

        return any(wildcard in user_permissions for wildcard in wildcards_to_check)

    @staticmethod
    def get_effective_permissions_from_roles(
        roles: List[Role], role_permissions_map: dict[UUID, List[Permission]]
    ) -> Set[str]:
        """
        Get effective permissions from roles, filtering active permissions.
        
        Used in: RBACService, RoleInheritanceService
        """
        effective_permissions = set()

        for role in roles:
            if not role.is_active:
                continue

            role_perms = role_permissions_map.get(role.id, [])
            for permission in role_perms:
                if permission.is_active:
                    effective_permissions.add(permission.get_full_name())

        return effective_permissions

    @staticmethod
    def create_permission_string(resource_type: str, action: str) -> str:
        """Create standardized permission string format."""
        return f"{resource_type}:{action}"

    @staticmethod
    def validate_authorization_context(context: AuthorizationContext) -> bool:
        """
        Validate that authorization context has required fields.
        
        Used in: AuthorizationService, ABACService, RBACService
        """
        if not context.user_id:
            return False
        if not context.resource_type:
            return False
        if not context.action:
            return False
        return True

    @staticmethod
    def extract_resource_and_action(permission_string: str) -> tuple[str, str]:
        """
        Extract resource type and action from permission string.
        
        Used in: RBACService, PolicyEvaluationService
        """
        if ":" not in permission_string:
            return permission_string, ""
        
        parts = permission_string.split(":", 1)
        return parts[0], parts[1]

    @staticmethod
    def check_resource_ownership(
        resource_owner_id: UUID, user_id: UUID
    ) -> bool:
        """
        Check if user owns the resource.
        
        Used in: ABACService, DocumentAuthorizationService
        """
        return resource_owner_id == user_id

    @staticmethod
    def check_organization_membership(
        resource_org_id: Optional[UUID], user_org_id: Optional[UUID]
    ) -> bool:
        """
        Check if resource belongs to user's organization.
        
        Used in: ABACService, DocumentAuthorizationService
        """
        if not resource_org_id or not user_org_id:
            return False
        return resource_org_id == user_org_id

    @staticmethod
    def get_wildcard_variations(permission: str) -> List[str]:
        """
        Get all wildcard variations of a permission.
        
        Returns: [exact_permission, resource_wildcard, action_wildcard, global_wildcard]
        """
        if ":" not in permission:
            return [permission, "*"]

        resource_type, action = permission.split(":", 1)
        return [
            permission,  # exact match
            f"{resource_type}:*",  # resource wildcard
            f"*:{action}",  # action wildcard
            "*:*",  # global wildcard
        ]

    @staticmethod
    def filter_active_permissions(permissions: List[Permission]) -> List[Permission]:
        """Filter out inactive permissions."""
        return [p for p in permissions if p.is_active]

    @staticmethod
    def filter_active_roles(roles: List[Role]) -> List[Role]:
        """Filter out inactive roles."""
        return [r for r in roles if r.is_active]