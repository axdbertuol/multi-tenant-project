"""Permission and role mapping utilities for IAM services."""

from typing import Dict, List, Set, Optional, Tuple
from uuid import UUID

from ...entities.role import Role
from ...entities.permission import Permission
from ...entities.user import User


class RolePermissionMapper:
    """Utility for mapping roles to permissions and calculating effective permissions."""

    @staticmethod
    def build_role_permissions_map(
        roles: List[Role],
        role_permissions_getter: callable
    ) -> Dict[UUID, List[Permission]]:
        """
        Build mapping of role IDs to their permissions.
        
        Used in: RBACService, RoleInheritanceService
        """
        role_permissions_map = {}
        
        for role in roles:
            if role.is_active:
                permissions = role_permissions_getter(role.id)
                # Filter to only active permissions
                active_permissions = [p for p in permissions if p.is_active]
                role_permissions_map[role.id] = active_permissions
        
        return role_permissions_map

    @staticmethod
    def calculate_effective_permissions(
        user_roles: List[Role],
        role_permissions_map: Dict[UUID, List[Permission]]
    ) -> Set[str]:
        """
        Calculate effective permissions for a user based on their roles.
        
        Used in: RBACService, AuthorizationService
        """
        effective_permissions = set()
        
        for role in user_roles:
            if not role.is_active:
                continue
                
            permissions = role_permissions_map.get(role.id, [])
            for permission in permissions:
                if permission.is_active:
                    effective_permissions.add(permission.get_full_name())
        
        return effective_permissions

    @staticmethod
    def calculate_inherited_permissions(
        base_permissions: Set[str],
        inherited_role_permissions: Dict[UUID, List[Permission]]
    ) -> Set[str]:
        """
        Calculate inherited permissions from parent roles.
        
        Used in: RoleInheritanceService
        """
        all_permissions = base_permissions.copy()
        
        for permissions in inherited_role_permissions.values():
            for permission in permissions:
                if permission.is_active:
                    all_permissions.add(permission.get_full_name())
        
        return all_permissions

    @staticmethod
    def group_permissions_by_resource(
        permissions: List[Permission]
    ) -> Dict[str, List[Permission]]:
        """
        Group permissions by resource type.
        
        Used in: PolicyEvaluationService, RBACService
        """
        grouped = {}
        
        for permission in permissions:
            resource_type = permission.resource_type
            if resource_type not in grouped:
                grouped[resource_type] = []
            grouped[resource_type].append(permission)
        
        return grouped

    @staticmethod
    def group_permissions_by_action(
        permissions: List[Permission]
    ) -> Dict[str, List[Permission]]:
        """
        Group permissions by action type.
        
        Used in: PolicyEvaluationService, AuthorizationService
        """
        grouped = {}
        
        for permission in permissions:
            action = permission.action.value if hasattr(permission.action, 'value') else str(permission.action)
            if action not in grouped:
                grouped[action] = []
            grouped[action].append(permission)
        
        return grouped

    @staticmethod
    def filter_permissions_by_resource_type(
        permissions: List[Permission],
        resource_type: str
    ) -> List[Permission]:
        """
        Filter permissions for a specific resource type.
        
        Used in: RBACService, PolicyEvaluationService
        """
        return [p for p in permissions if p.resource_type == resource_type]

    @staticmethod
    def filter_permissions_by_action(
        permissions: List[Permission],
        action: str
    ) -> List[Permission]:
        """
        Filter permissions for a specific action.
        
        Used in: RBACService, PolicyEvaluationService
        """
        return [
            p for p in permissions 
            if (hasattr(p.action, 'value') and p.action.value == action) or str(p.action) == action
        ]

    @staticmethod
    def get_permission_hierarchy(
        permissions: List[Permission]
    ) -> Dict[str, List[str]]:
        """
        Get permission hierarchy (resource types and their actions).
        
        Used in: PolicyEvaluationService, AuthorizationService
        """
        hierarchy = {}
        
        for permission in permissions:
            resource_type = permission.resource_type
            action = permission.action.value if hasattr(permission.action, 'value') else str(permission.action)
            
            if resource_type not in hierarchy:
                hierarchy[resource_type] = []
            
            if action not in hierarchy[resource_type]:
                hierarchy[resource_type].append(action)
        
        return hierarchy

    @staticmethod
    def merge_permission_sets(
        *permission_sets: Set[str]
    ) -> Set[str]:
        """
        Merge multiple permission sets.
        
        Used in: RoleInheritanceService, AuthorizationService
        """
        merged = set()
        for perm_set in permission_sets:
            merged.update(perm_set)
        return merged

    @staticmethod
    def check_permission_conflicts(
        permissions: List[Permission]
    ) -> List[Tuple[Permission, Permission]]:
        """
        Check for permission conflicts (e.g., allow and deny for same resource:action).
        
        Used in: PolicyEvaluationService, RoleInheritanceService
        """
        conflicts = []
        permission_map = {}
        
        for permission in permissions:
            key = f"{permission.resource_type}:{permission.action}"
            if key not in permission_map:
                permission_map[key] = []
            permission_map[key].append(permission)
        
        # Check for conflicts within each resource:action group
        for key, perms in permission_map.items():
            if len(perms) > 1:
                # Check if there are different effects (allow/deny)
                effects = set()
                for perm in perms:
                    if hasattr(perm, 'effect'):
                        effects.add(perm.effect)
                
                if len(effects) > 1:
                    # Add all pairs as conflicts
                    for i in range(len(perms)):
                        for j in range(i + 1, len(perms)):
                            conflicts.append((perms[i], perms[j]))
        
        return conflicts

    @staticmethod
    def deduplicate_permissions(
        permissions: List[Permission]
    ) -> List[Permission]:
        """
        Remove duplicate permissions based on resource_type:action.
        
        Used in: RBACService, RoleInheritanceService
        """
        seen = set()
        unique_permissions = []
        
        for permission in permissions:
            key = f"{permission.resource_type}:{permission.action}"
            if key not in seen:
                seen.add(key)
                unique_permissions.append(permission)
        
        return unique_permissions

    @staticmethod
    def expand_wildcard_permissions(
        permissions: List[str],
        available_resources: List[str] = None,
        available_actions: List[str] = None
    ) -> List[str]:
        """
        Expand wildcard permissions to explicit permissions.
        
        Used in: RBACService, AuthorizationService
        """
        expanded = set()
        
        for permission in permissions:
            if "*:*" in permission:
                # Global wildcard - add all possible combinations
                if available_resources and available_actions:
                    for resource in available_resources:
                        for action in available_actions:
                            expanded.add(f"{resource}:{action}")
                else:
                    expanded.add(permission)  # Keep as-is if no expansion data
            elif ":*" in permission:
                # Resource wildcard
                resource_type = permission.split(":")[0]
                if available_actions:
                    for action in available_actions:
                        expanded.add(f"{resource_type}:{action}")
                else:
                    expanded.add(permission)  # Keep as-is if no expansion data
            elif "*:" in permission:
                # Action wildcard
                action = permission.split(":")[1]
                if available_resources:
                    for resource in available_resources:
                        expanded.add(f"{resource}:{action}")
                else:
                    expanded.add(permission)  # Keep as-is if no expansion data
            else:
                # Exact permission
                expanded.add(permission)
        
        return list(expanded)

    @staticmethod
    def get_minimal_permission_set(
        permissions: List[str]
    ) -> List[str]:
        """
        Get minimal set of permissions by removing redundant ones.
        
        For example, if "*:*" is present, other permissions are redundant.
        
        Used in: RBACService, AuthorizationService
        """
        permission_set = set(permissions)
        
        # If global wildcard exists, return only that
        if "*:*" in permission_set:
            return ["*:*"]
        
        # Remove redundant permissions
        minimal = set()
        
        for permission in permission_set:
            is_redundant = False
            
            # Check if this permission is covered by a wildcard
            if ":" in permission:
                resource_type, action = permission.split(":", 1)
                
                # Check if covered by resource wildcard
                if f"{resource_type}:*" in permission_set:
                    is_redundant = True
                
                # Check if covered by action wildcard
                if f"*:{action}" in permission_set:
                    is_redundant = True
            
            if not is_redundant:
                minimal.add(permission)
        
        return list(minimal)


class UserRoleMapper:
    """Utility for mapping users to roles and calculating effective roles."""

    @staticmethod
    def build_user_roles_map(
        users: List[User],
        user_roles_getter: callable
    ) -> Dict[UUID, List[Role]]:
        """
        Build mapping of user IDs to their roles.
        
        Used in: RBACService, MembershipService
        """
        user_roles_map = {}
        
        for user in users:
            if user.is_active:
                roles = user_roles_getter(user.id)
                # Filter to only active roles
                active_roles = [r for r in roles if r.is_active]
                user_roles_map[user.id] = active_roles
        
        return user_roles_map

    @staticmethod
    def get_users_by_role(
        role_id: UUID,
        user_roles_map: Dict[UUID, List[Role]]
    ) -> List[UUID]:
        """
        Get all users who have a specific role.
        
        Used in: RBACService, MembershipService
        """
        users_with_role = []
        
        for user_id, roles in user_roles_map.items():
            if any(role.id == role_id for role in roles):
                users_with_role.append(user_id)
        
        return users_with_role

    @staticmethod
    def get_roles_by_user(
        user_id: UUID,
        user_roles_map: Dict[UUID, List[Role]]
    ) -> List[Role]:
        """
        Get all roles for a specific user.
        
        Used in: RBACService, MembershipService
        """
        return user_roles_map.get(user_id, [])

    @staticmethod
    def calculate_role_usage_stats(
        user_roles_map: Dict[UUID, List[Role]]
    ) -> Dict[UUID, int]:
        """
        Calculate usage statistics for each role.
        
        Used in: MembershipService, OrganizationDomainService
        """
        role_usage = {}
        
        for user_id, roles in user_roles_map.items():
            for role in roles:
                if role.id not in role_usage:
                    role_usage[role.id] = 0
                role_usage[role.id] += 1
        
        return role_usage