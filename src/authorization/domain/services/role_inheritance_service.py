from typing import List, Set, Dict, Optional
from uuid import UUID

from ..entities.role import Role
from ..entities.permission import Permission


class RoleInheritanceService:
    """Service for handling role inheritance and permission calculation."""
    
    def calculate_inherited_permissions(
        self, 
        role: Role, 
        all_roles: List[Role], 
        role_permissions: Dict[UUID, List[Permission]]
    ) -> List[Permission]:
        """
        Calculate all permissions for a role including inherited permissions.
        
        Args:
            role: The role to calculate permissions for
            all_roles: All available roles in the system
            role_permissions: Map of role_id to direct permissions
            
        Returns:
            List of all permissions (direct + inherited)
        """
        if not role.has_parent():
            return role_permissions.get(role.id, [])
        
        # Get role hierarchy path (from root to current role)
        hierarchy_path = role.get_role_hierarchy_path(all_roles)
        
        # Collect permissions from all roles in hierarchy
        all_permissions = []
        seen_permissions = set()  # Track to avoid duplicates
        
        # Start from root and work down to ensure proper inheritance order
        for role_id in hierarchy_path:
            direct_permissions = role_permissions.get(role_id, [])
            
            for permission in direct_permissions:
                # Use permission action + resource_type as unique key
                permission_key = f"{permission.action}:{permission.resource_type}"
                
                if permission_key not in seen_permissions:
                    all_permissions.append(permission)
                    seen_permissions.add(permission_key)
        
        return all_permissions
    
    def get_role_hierarchy(self, role: Role, all_roles: List[Role]) -> List[Role]:
        """
        Get complete role hierarchy for a given role.
        
        Returns list of roles from root ancestor to the given role.
        """
        if not role.has_parent():
            return [role]
        
        role_map = {r.id: r for r in all_roles}
        hierarchy = []
        
        # Get hierarchy path
        hierarchy_path = role.get_role_hierarchy_path(all_roles)
        
        # Convert IDs to Role objects
        for role_id in hierarchy_path:
            if role_id in role_map:
                hierarchy.append(role_map[role_id])
        
        return hierarchy
    
    def get_child_roles(self, parent_role_id: UUID, all_roles: List[Role]) -> List[Role]:
        """Get all direct child roles of a parent role."""
        return [role for role in all_roles if role.parent_role_id == parent_role_id]
    
    def get_descendant_roles(self, ancestor_role_id: UUID, all_roles: List[Role]) -> List[Role]:
        """Get all descendant roles (children, grandchildren, etc.) of a role."""
        descendants = []
        
        # Get direct children
        children = self.get_child_roles(ancestor_role_id, all_roles)
        
        for child in children:
            descendants.append(child)
            # Recursively get descendants of child
            descendants.extend(self.get_descendant_roles(child.id, all_roles))
        
        return descendants
    
    def validate_role_hierarchy(self, roles: List[Role]) -> List[str]:
        """
        Validate entire role hierarchy for issues.
        
        Returns list of validation errors.
        """
        errors = []
        
        for role in roles:
            is_valid, message = role.validate_inheritance_rules(roles)
            if not is_valid:
                errors.append(f"Role {role.name.value}: {message}")
        
        # Check for orphaned roles (parent_role_id points to non-existent role)
        role_ids = {role.id for role in roles}
        for role in roles:
            if role.parent_role_id and role.parent_role_id not in role_ids:
                errors.append(f"Role {role.name.value}: Parent role {role.parent_role_id} not found")
        
        return errors
    
    def build_role_tree(self, roles: List[Role]) -> Dict[UUID, List[Role]]:
        """
        Build a tree structure of roles organized by parent.
        
        Returns dict where key is parent_role_id and value is list of child roles.
        """
        tree = {}
        
        for role in roles:
            parent_id = role.parent_role_id or "root"
            
            if parent_id not in tree:
                tree[parent_id] = []
            
            tree[parent_id].append(role)
        
        return tree
    
    def get_effective_permissions_for_user_roles(
        self, 
        user_role_ids: List[UUID], 
        all_roles: List[Role], 
        role_permissions: Dict[UUID, List[Permission]]
    ) -> List[Permission]:
        """
        Calculate effective permissions for a user with multiple roles.
        
        Combines permissions from all roles including inherited permissions.
        """
        all_permissions = []
        seen_permissions = set()
        
        for role_id in user_role_ids:
            role = next((r for r in all_roles if r.id == role_id), None)
            if not role or not role.is_active:
                continue
            
            # Get permissions for this role (including inherited)
            role_perms = self.calculate_inherited_permissions(role, all_roles, role_permissions)
            
            for permission in role_perms:
                permission_key = f"{permission.action}:{permission.resource_type}"
                
                if permission_key not in seen_permissions:
                    all_permissions.append(permission)
                    seen_permissions.add(permission_key)
        
        return all_permissions
    
    def can_role_inherit_from(
        self, 
        child_role: Role, 
        potential_parent_role: Role, 
        all_roles: List[Role]
    ) -> tuple[bool, str]:
        """
        Check if a role can inherit from another role.
        
        Returns (can_inherit, reason)
        """
        # Basic checks
        if child_role.id == potential_parent_role.id:
            return False, "Role cannot inherit from itself"
        
        if child_role.is_system_role:
            return False, "System roles cannot inherit from other roles"
        
        if not potential_parent_role.is_active:
            return False, "Cannot inherit from inactive role"
        
        # Check for circular inheritance
        temp_role = child_role.set_parent_role(potential_parent_role.id)
        if temp_role.is_descendant_of(all_roles + [temp_role], child_role.id):
            return False, "Would create circular inheritance"
        
        # Check organization scope
        if child_role.organization_id and potential_parent_role.organization_id:
            if child_role.organization_id != potential_parent_role.organization_id:
                return False, "Child role must be in same organization as parent"
        elif not child_role.organization_id and potential_parent_role.organization_id:
            return False, "Global role cannot inherit from organization role"
        
        return True, "Inheritance is allowed"