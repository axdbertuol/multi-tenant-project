import pytest
from datetime import datetime
from uuid import uuid4, UUID
from typing import List, Dict

from authorization.domain.entities.role import Role
from src.authorization.domain.entities.permission import Permission, PermissionAction
from authorization.domain.services.role_inheritance_service import (
    RoleInheritanceService,
)
from authorization.domain.value_objects.role_name import RoleName


class TestRoleInheritanceEdgeCases:
    """Edge test cases for role inheritance scenarios, including Default_RH inheritance patterns."""

    def setup_method(self):
        """Set up test fixtures with complex role hierarchy."""
        self.service = RoleInheritanceService()
        self.creator_id = uuid4()
        self.org_id = uuid4()

        # Create base Default_RH role with common permissions
        self.default_rh_role = Role.create(
            name="Default_RH",
            description="Default role with common HR permissions",
            created_by=self.creator_id,
            organization_id=self.org_id,
        )

        # Create permissions for Default_RH
        self.default_rh_permissions = [
            Permission.create(
                "read_users", "Read user profiles", PermissionAction.READ, "user"
            ),
            Permission.create(
                "update_user_basic",
                "Update basic user info",
                PermissionAction.UPDATE,
                "user_basic",
            ),
            Permission.create(
                "read_organizations",
                "Read organization data",
                PermissionAction.READ,
                "organization",
            ),
            Permission.create(
                "create_reports",
                "Create basic reports",
                PermissionAction.CREATE,
                "report",
            ),
            Permission.create(
                "read_attendance",
                "Read attendance records",
                PermissionAction.READ,
                "attendance",
            ),
        ]

        # Create enhanced HR role inheriting from Default_RH
        self.enhanced_hr_role = Role.create(
            name="Enhanced_HR",
            description="Enhanced HR role with additional permissions",
            created_by=self.creator_id,
            organization_id=self.org_id,
            parent_role_id=self.default_rh_role.id,
        )

        # Additional permissions for Enhanced_HR
        self.enhanced_hr_permissions = [
            Permission.create(
                "delete_users", "Delete user accounts", PermissionAction.DELETE, "user"
            ),
            Permission.create(
                "manage_payroll",
                "Manage payroll data",
                PermissionAction.MANAGE,
                "payroll",
            ),
            Permission.create(
                "execute_bulk_operations",
                "Execute bulk user operations",
                PermissionAction.EXECUTE,
                "user_bulk",
            ),
            Permission.create(
                "create_policies",
                "Create HR policies",
                PermissionAction.CREATE,
                "policy",
            ),
        ]

    def test_basic_role_inheritance_permissions(self):
        """Test that Enhanced_HR inherits all Default_RH permissions plus its own."""
        all_roles = [self.default_rh_role, self.enhanced_hr_role]
        role_permissions = {
            self.default_rh_role.id: self.default_rh_permissions,
            self.enhanced_hr_role.id: self.enhanced_hr_permissions,
        }

        effective_permissions = self.service.calculate_inherited_permissions(
            self.enhanced_hr_role, all_roles, role_permissions
        )

        # Should have all Default_RH permissions + Enhanced_HR permissions
        expected_count = len(self.default_rh_permissions) + len(
            self.enhanced_hr_permissions
        )
        assert len(effective_permissions) == expected_count

        # Verify specific permissions are present
        permission_names = [p.name.value for p in effective_permissions]
        assert "read_users" in permission_names  # From Default_RH
        assert "delete_users" in permission_names  # From Enhanced_HR
        assert "manage_payroll" in permission_names  # From Enhanced_HR

    def test_three_level_inheritance_chain(self):
        """Test inheritance through three levels: Default_RH -> Enhanced_HR -> Super_HR."""
        # Create Super_HR role inheriting from Enhanced_HR
        super_hr_role = Role.create(
            name="Super_HR",
            description="Super HR role with all permissions",
            created_by=self.creator_id,
            organization_id=self.org_id,
            parent_role_id=self.enhanced_hr_role.id,
        )

        super_hr_permissions = [
            Permission.create(
                "delete_organizations",
                "Delete organizations",
                PermissionAction.DELETE,
                "organization",
            ),
            Permission.create(
                "manage_system_settings",
                "Manage system settings",
                PermissionAction.MANAGE,
                "system",
            ),
            Permission.create(
                "execute_admin_commands",
                "Execute admin commands",
                PermissionAction.EXECUTE,
                "admin",
            ),
        ]

        all_roles = [self.default_rh_role, self.enhanced_hr_role, super_hr_role]
        role_permissions = {
            self.default_rh_role.id: self.default_rh_permissions,
            self.enhanced_hr_role.id: self.enhanced_hr_permissions,
            super_hr_role.id: super_hr_permissions,
        }

        effective_permissions = self.service.calculate_inherited_permissions(
            super_hr_role, all_roles, role_permissions
        )

        # Should have permissions from all three levels
        expected_count = (
            len(self.default_rh_permissions)
            + len(self.enhanced_hr_permissions)
            + len(super_hr_permissions)
        )
        assert len(effective_permissions) == expected_count

        # Verify hierarchy path
        hierarchy_path = super_hr_role.get_role_hierarchy_path(all_roles)
        assert len(hierarchy_path) == 3
        assert hierarchy_path[0] == self.default_rh_role.id  # Root
        assert hierarchy_path[1] == self.enhanced_hr_role.id  # Middle
        assert hierarchy_path[2] == super_hr_role.id  # Leaf

    def test_duplicate_permission_handling_in_inheritance(self):
        """Test that duplicate permissions are handled correctly in inheritance."""
        # Create a role with overlapping permissions
        conflicting_role = Role.create(
            name="Conflicting_HR",
            description="Role with some overlapping permissions",
            created_by=self.creator_id,
            organization_id=self.org_id,
            parent_role_id=self.default_rh_role.id,
        )

        # Add some permissions that overlap with Default_RH
        conflicting_permissions = [
            Permission.create(
                "read_users",
                "Read user profiles (duplicate)",
                PermissionAction.READ,
                "user",
            ),  # Duplicate
            Permission.create(
                "new_permission",
                "A new unique permission",
                PermissionAction.CREATE,
                "new_resource",
            ),
        ]

        all_roles = [self.default_rh_role, conflicting_role]
        role_permissions = {
            self.default_rh_role.id: self.default_rh_permissions,
            conflicting_role.id: conflicting_permissions,
        }

        effective_permissions = self.service.calculate_inherited_permissions(
            conflicting_role, all_roles, role_permissions
        )

        # Should not have duplicates
        permission_keys = [
            f"{p.action.value}:{p.resource_type}" for p in effective_permissions
        ]
        assert len(permission_keys) == len(set(permission_keys))  # No duplicates

        # Should have parent permissions + unique child permissions
        expected_unique_permissions = (
            len(self.default_rh_permissions) + 1
        )  # +1 for new_permission
        assert len(effective_permissions) == expected_unique_permissions

    def test_circular_inheritance_detection(self):
        """Test detection and prevention of circular inheritance."""
        # Create roles that would form a circle
        role_a = Role.create("Role_A", "First role", self.creator_id, self.org_id)
        role_b = Role.create(
            "Role_B",
            "Second role",
            self.creator_id,
            self.org_id,
            parent_role_id=role_a.id,
        )

        # Try to make role_a inherit from role_b (creating a circle)
        all_roles = [role_a, role_b]

        can_inherit, reason = self.service.can_role_inherit_from(
            role_a, role_b, all_roles
        )
        assert can_inherit is False
        assert "circular inheritance" in reason.lower()

    def test_deep_inheritance_chain_with_cycles_prevention(self):
        """Test deep inheritance chains and cycle prevention."""
        # Create a deep chain: Root -> L1 -> L2 -> L3 -> L4 -> L5
        roles = []
        parent_id = None

        for i in range(6):
            role = Role.create(
                f"Level_{i}",
                f"Role at level {i}",
                self.creator_id,
                self.org_id,
                parent_role_id=parent_id,
            )
            roles.append(role)
            parent_id = role.id

        # Verify deep inheritance works
        deepest_role = roles[-1]
        hierarchy_path = deepest_role.get_role_hierarchy_path(roles)
        assert len(hierarchy_path) == 6

        # Try to create a cycle by making root inherit from deepest
        can_inherit, reason = self.service.can_role_inherit_from(
            roles[0], deepest_role, roles
        )
        assert can_inherit is False
        assert "circular inheritance" in reason.lower()

    def test_orphaned_role_detection(self):
        """Test detection of roles with missing parent references."""
        orphaned_role = Role.create(
            "Orphaned_Role",
            "Role with missing parent",
            self.creator_id,
            self.org_id,
            parent_role_id=uuid4(),  # Non-existent parent
        )

        all_roles = [self.default_rh_role, orphaned_role]
        errors = self.service.validate_role_hierarchy(all_roles)

        assert len(errors) > 0
        assert any("Parent role" in error and "not found" in error for error in errors)

    def test_cross_organization_inheritance_restrictions(self):
        """Test that roles cannot inherit across organizations."""
        other_org_id = uuid4()

        # Create role in different organization
        other_org_role = Role.create(
            "Other_Org_Role",
            "Role in different organization",
            self.creator_id,
            other_org_id,
        )

        # Try to make Default_RH inherit from other org role
        can_inherit, reason = self.service.can_role_inherit_from(
            self.default_rh_role, other_org_role, [self.default_rh_role, other_org_role]
        )

        assert can_inherit is False
        assert "same organization" in reason

    def test_global_to_organization_inheritance(self):
        """Test that organization roles can inherit from global roles."""
        # Create global role (no organization)
        global_role = Role.create(
            "Global_Base",
            "Global base role",
            self.creator_id,
            organization_id=None,  # Global role
        )

        # Create organization role inheriting from global
        org_role = Role.create(
            "Org_Specific",
            "Organization-specific role",
            self.creator_id,
            self.org_id,
            parent_role_id=global_role.id,
        )

        all_roles = [global_role, org_role]
        can_inherit, reason = self.service.can_role_inherit_from(
            org_role, global_role, all_roles
        )

        assert can_inherit is True

    def test_system_role_inheritance_restrictions(self):
        """Test that system roles cannot be modified or inherit."""
        system_role = Role.create(
            "System_Admin",
            "System administrator role",
            self.creator_id,
            is_system_role=True,
        )

        # System roles cannot inherit from others
        can_inherit, reason = self.service.can_role_inherit_from(
            system_role, self.default_rh_role, [system_role, self.default_rh_role]
        )
        assert can_inherit is False
        assert "System roles cannot inherit" in reason

        # Cannot set parent on system role
        with pytest.raises(ValueError, match="System roles cannot inherit"):
            system_role.set_parent_role(self.default_rh_role.id)

    def test_inactive_parent_role_inheritance(self):
        """Test that roles cannot inherit from inactive parents."""
        # Deactivate Default_RH
        inactive_role = self.default_rh_role.deactivate()

        # Try to create new role inheriting from inactive role
        can_inherit, reason = self.service.can_role_inherit_from(
            self.enhanced_hr_role, inactive_role, [inactive_role, self.enhanced_hr_role]
        )

        assert can_inherit is False
        assert "inactive role" in reason.lower()

    def test_permission_override_precedence_in_inheritance(self):
        """Test that child role permissions take precedence over inherited ones."""
        # Create permission with same action+resource but different description
        override_permission = Permission.create(
            "read_users_enhanced",
            "Enhanced user reading capability",
            PermissionAction.READ,
            "user",  # Same resource type
        )

        child_role = Role.create(
            "Child_With_Override",
            "Child role with permission override",
            self.creator_id,
            self.org_id,
            parent_role_id=self.default_rh_role.id,
        )

        all_roles = [self.default_rh_role, child_role]
        role_permissions = {
            self.default_rh_role.id: self.default_rh_permissions,
            child_role.id: [override_permission],
        }

        effective_permissions = self.service.calculate_inherited_permissions(
            child_role, all_roles, role_permissions
        )

        # Should not have duplicate read:user permissions
        read_user_perms = [
            p
            for p in effective_permissions
            if p.resource_type == "user" and p.action == PermissionAction.READ
        ]
        assert len(read_user_perms) == 1  # Only one read:user permission

    def test_multi_parent_simulation_through_composition(self):
        """Test simulating multiple inheritance through role composition."""
        # Create two base roles with different permission sets
        finance_role = Role.create(
            "Finance_Base", "Base finance permissions", self.creator_id, self.org_id
        )
        hr_role = Role.create(
            "HR_Base", "Base HR permissions", self.creator_id, self.org_id
        )

        # Create permissions for each
        finance_permissions = [
            Permission.create(
                "read_finances", "Read financial data", PermissionAction.READ, "finance"
            ),
            Permission.create(
                "create_budgets", "Create budgets", PermissionAction.CREATE, "budget"
            ),
        ]

        hr_permissions = [
            Permission.create(
                "manage_employees",
                "Manage employees",
                PermissionAction.MANAGE,
                "employee",
            ),
            Permission.create(
                "read_hr_reports", "Read HR reports", PermissionAction.READ, "hr_report"
            ),
        ]

        # Create composite role that inherits from HR but needs Finance permissions too
        composite_role = Role.create(
            "Finance_HR_Manager",
            "Role needing both Finance and HR permissions",
            self.creator_id,
            self.org_id,
            parent_role_id=hr_role.id,
        )

        # Add finance permissions directly to composite role (simulating multi-inheritance)
        composite_permissions = finance_permissions.copy()

        all_roles = [finance_role, hr_role, composite_role]
        role_permissions = {
            finance_role.id: finance_permissions,
            hr_role.id: hr_permissions,
            composite_role.id: composite_permissions,
        }

        effective_permissions = self.service.calculate_inherited_permissions(
            composite_role, all_roles, role_permissions
        )

        # Should have HR permissions (inherited) + Finance permissions (direct)
        expected_count = len(hr_permissions) + len(finance_permissions)
        assert len(effective_permissions) == expected_count

        permission_names = [p.name.value for p in effective_permissions]
        assert "manage_employees" in permission_names  # From HR (inherited)
        assert "read_finances" in permission_names  # From Finance (direct)

    def test_role_hierarchy_with_missing_intermediate_roles(self):
        """Test hierarchy resilience when intermediate roles are missing."""
        # Create grandparent, parent, and child
        grandparent = Role.create(
            "Grandparent", "Grandparent role", self.creator_id, self.org_id
        )
        parent = Role.create(
            "Parent",
            "Parent role",
            self.creator_id,
            self.org_id,
            parent_role_id=grandparent.id,
        )
        child = Role.create(
            "Child",
            "Child role",
            self.creator_id,
            self.org_id,
            parent_role_id=parent.id,
        )

        # Simulate missing parent role in hierarchy lookup
        incomplete_roles = [grandparent, child]  # Missing parent

        # Should handle gracefully
        hierarchy_path = child.get_role_hierarchy_path(incomplete_roles)
        # Should only include roles that exist in the provided list
        assert len(hierarchy_path) <= 2

    def test_permission_inheritance_with_large_role_tree(self):
        """Test performance and correctness with large role hierarchies."""
        # Create a wide and deep role tree
        root_role = Role.create("Root", "Root role", self.creator_id, self.org_id)
        all_roles = [root_role]
        role_permissions = {
            root_role.id: [
                Permission.create(
                    "root_perm", "Root permission", PermissionAction.READ, "root"
                )
            ]
        }

        # Create 3 levels with 3 children each
        current_level = [root_role]

        for level in range(3):
            next_level = []
            for parent in current_level:
                for i in range(3):
                    child = Role.create(
                        f"Level_{level}_Child_{i}_",
                        f"Child {i} of ",
                        self.creator_id,
                        self.org_id,
                        parent_role_id=parent.id,
                    )

                    # Add unique permission to each child
                    child_perm = Permission.create(
                        f"perm_{level}_{i}",
                        f"Permission for level {level} child {i}",
                        PermissionAction.CREATE,
                        f"resource_{level}_{i}",
                    )

                    all_roles.append(child)
                    role_permissions[child.id] = [child_perm]
                    next_level.append(child)

            current_level = next_level

        # Test deepest role has all permissions from its hierarchy
        deepest_role = current_level[0]  # Pick first role from deepest level

        effective_permissions = self.service.calculate_inherited_permissions(
            deepest_role, all_roles, role_permissions
        )

        # Should have permissions from all levels in its path
        hierarchy_path = deepest_role.get_role_hierarchy_path(all_roles)
        expected_permission_count = len(
            hierarchy_path
        )  # One permission per role in path

        assert len(effective_permissions) == expected_permission_count

    def test_role_deletion_impact_on_inheritance(self):
        """Test impact of role deletion on inheritance chains."""
        # Create chain: A -> B -> C
        role_a = Role.create("Role_A", "Role A", self.creator_id, self.org_id)
        role_b = Role.create(
            "Role_B", "Role B", self.creator_id, self.org_id, parent_role_id=role_a.id
        )
        role_c = Role.create(
            "Role_C", "Role C", self.creator_id, self.org_id, parent_role_id=role_b.id
        )

        all_roles = [role_a, role_b, role_c]

        # Verify initial hierarchy
        assert role_c.get_role_hierarchy_path(all_roles) == [
            role_a.id,
            role_b.id,
            role_c.id,
        ]

        # Simulate deletion of role_b
        roles_after_deletion = [role_a, role_c]  # role_b removed

        # Validate hierarchy identifies the break
        errors = self.service.validate_role_hierarchy(roles_after_deletion)
        assert any(
            "Parent role" in error and str(role_b.id) in error for error in errors
        )

    def test_permission_conflicts_in_complex_inheritance(self):
        """Test handling of permission conflicts in complex inheritance scenarios."""
        # Create scenario where multiple inheritance paths could create conflicts

        # Base roles with conflicting permission interpretations
        base_read_role = Role.create(
            "Base_Reader", "Base reader role", self.creator_id, self.org_id
        )
        base_write_role = Role.create(
            "Base_Writer", "Base writer role", self.creator_id, self.org_id
        )

        # Child role that could inherit conflicting interpretations
        composite_child = Role.create(
            "Composite_Child",
            "Child with potential conflicts",
            self.creator_id,
            self.org_id,
            parent_role_id=base_read_role.id,
        )

        # Create permissions that could conflict
        read_perm = Permission.create(
            "access_data", "Read access to data", PermissionAction.READ, "data"
        )
        write_perm = Permission.create(
            "access_data_write", "Write access to data", PermissionAction.UPDATE, "data"
        )

        all_roles = [base_read_role, base_write_role, composite_child]
        role_permissions = {
            base_read_role.id: [read_perm],
            composite_child.id: [
                write_perm
            ],  # Child adds write permission to same resource
        }

        effective_permissions = self.service.calculate_inherited_permissions(
            composite_child, all_roles, role_permissions
        )

        # Should have both read and write permissions for same resource
        data_permissions = [
            p for p in effective_permissions if p.resource_type == "data"
        ]
        assert len(data_permissions) == 2  # Both read and write

        perm_types = {p.action for p in data_permissions}
        assert PermissionAction.READ in perm_types
        assert PermissionAction.UPDATE in perm_types
