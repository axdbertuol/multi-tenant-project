from typing import List, Optional, Dict
from uuid import UUID

from ..entities.authorization_context import AuthorizationContext
from ..entities.permission import Permission
from ..repositories.role_repository import RoleRepository
from ..repositories.permission_repository import PermissionRepository
from ..repositories.role_permission_repository import RolePermissionRepository
from ..value_objects.authorization_decision import AuthorizationDecision, DecisionReason
from .role_inheritance_service import RoleInheritanceService


class RBACService:
    """Role-Based Access Control service."""

    def __init__(
        self,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
        role_permission_repository: RolePermissionRepository,
        role_inheritance_service: Optional[RoleInheritanceService] = None,
    ):
        self._role_repository = role_repository
        self._permission_repository = permission_repository
        self._role_permission_repository = role_permission_repository
        self._role_inheritance_service = (
            role_inheritance_service or RoleInheritanceService()
        )

    def authorize(self, context: AuthorizationContext) -> AuthorizationDecision:
        """Authorize request using RBAC."""
        reasons: List[DecisionReason] = []

        # Get user roles
        user_roles = self._role_repository.get_user_roles(
            context.user_id, context.organization_id
        )

        if not user_roles:
            reason = DecisionReason(
                type="rbac_no_roles",
                message="User has no roles assigned",
                details={"user_id": str(context.user_id)},
            )
            return AuthorizationDecision.deny([reason])

        # Get user permissions through roles
        user_permissions = self.get_user_permissions(
            context.user_id, context.organization_id
        )

        if not user_permissions:
            reason = DecisionReason(
                type="rbac_no_permissions",
                message="User has no permissions through assigned roles",
                details={
                    "user_id": str(context.user_id),
                    "roles": [role.name.value for role in user_roles],
                },
            )
            return AuthorizationDecision.deny([reason])

        # Check if user has required permission
        required_permission = f"{context.resource_type}:{context.action}"

        # Check exact permission match
        if required_permission in user_permissions:
            reason = DecisionReason(
                type="rbac_allow",
                message=f"User has required permission: {required_permission}",
                details={
                    "permission": required_permission,
                    "roles": [role.name.value for role in user_roles],
                },
            )
            return AuthorizationDecision.allow([reason])

        # Check wildcard permissions
        resource_wildcard = f"{context.resource_type}:*"
        if resource_wildcard in user_permissions:
            reason = DecisionReason(
                type="rbac_allow",
                message=f"User has wildcard permission for resource: {resource_wildcard}",
                details={
                    "permission": resource_wildcard,
                    "roles": [role.name.value for role in user_roles],
                },
            )
            return AuthorizationDecision.allow([reason])

        # Check action wildcard
        action_wildcard = f"*:{context.action}"
        if action_wildcard in user_permissions:
            reason = DecisionReason(
                type="rbac_allow",
                message=f"User has action wildcard permission: {action_wildcard}",
                details={
                    "permission": action_wildcard,
                    "roles": [role.name.value for role in user_roles],
                },
            )
            return AuthorizationDecision.allow([reason])

        # Check global wildcard
        if "*:*" in user_permissions:
            reason = DecisionReason(
                type="rbac_allow",
                message="User has global wildcard permission",
                details={
                    "permission": "*:*",
                    "roles": [role.name.value for role in user_roles],
                },
            )
            return AuthorizationDecision.allow([reason])

        # No matching permission found
        reason = DecisionReason(
            type="rbac_deny",
            message=f"User lacks required permission: {required_permission}",
            details={
                "required_permission": required_permission,
                "user_permissions": user_permissions,
                "roles": [role.name.value for role in user_roles],
            },
        )
        return AuthorizationDecision.deny([reason])

    def get_user_permissions(
        self, user_id: UUID, organization_id: Optional[UUID] = None
    ) -> List[str]:
        """Get all permissions for a user through their roles (including inherited permissions)."""
        # Get user roles
        user_roles = self._role_repository.get_user_roles(user_id, organization_id)

        if not user_roles:
            return []

        # Get all roles in the organization hierarchy
        all_roles = self._role_repository.get_role_hierarchy(organization_id)

        # Build role permissions map
        role_permissions_map: Dict[UUID, List[Permission]] = {}
        for role in all_roles:
            role_perms = self._permission_repository.get_role_permissions(role.id)
            # Only include active permissions
            active_perms = [p for p in role_perms if p.is_active]
            role_permissions_map[role.id] = active_perms

        # Get effective permissions for user roles (including inherited)
        user_role_ids = [role.id for role in user_roles if role.is_active]
        effective_permissions = (
            self._role_inheritance_service.get_effective_permissions_for_user_roles(
                user_role_ids, all_roles, role_permissions_map
            )
        )

        # Convert to permission name strings
        permission_names = set()
        for permission in effective_permissions:
            if permission.is_active:
                permission_names.add(permission.get_full_name())

        return list(permission_names)

    def user_has_permission(
        self,
        user_id: UUID,
        permission_name: str,
        organization_id: Optional[UUID] = None,
    ) -> bool:
        """Check if user has a specific permission."""
        user_permissions = self.get_user_permissions(user_id, organization_id)

        # Check exact match
        if permission_name in user_permissions:
            return True

        # Check wildcard matches
        resource_type, action = (
            permission_name.split(":", 1)
            if ":" in permission_name
            else (permission_name, "")
        )

        # Check resource wildcard
        resource_wildcard = f"{resource_type}:*"
        if resource_wildcard in user_permissions:
            return True

        # Check action wildcard
        if action:
            action_wildcard = f"*:{action}"
            if action_wildcard in user_permissions:
                return True

        # Check global wildcard
        if "*:*" in user_permissions:
            return True

        return False

    def get_user_roles_in_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> List[str]:
        """Get user role names in a specific organization."""
        roles = self._role_repository.get_user_roles_in_organization(user_id, organization_id)
        return [role.name.value for role in roles if role.is_active]

    def user_has_role(
        self, user_id: UUID, role_name: str, organization_id: Optional[UUID] = None
    ) -> bool:
        """Check if user has a specific role."""
        if organization_id:
            user_roles = self.get_user_roles_in_organization(user_id, organization_id)
        else:
            roles = self._role_repository.get_user_roles(user_id, organization_id)
            user_roles = [role.name.value for role in roles if role.is_active]
        return role_name in user_roles
