from pydantic import ValidationError
import pytest
from datetime import datetime, timezone
from uuid import uuid4, UUID

from authorization.domain.entities.role import Role
from authorization.domain.value_objects.role_name import RoleName


class TestRoleEdgeCases:
    """Edge test cases for Role entity focusing on inheritance and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.creator_id = uuid4()
        self.org_id = uuid4()

    def test_role_self_inheritance_prevention(self):
        """Test that roles cannot inherit from themselves."""
        role = Role.create(
            "Self_Role",
            "Role that tries to inherit from itself",
            self.creator_id,
            self.org_id,
        )

        with pytest.raises(ValueError, match="Role cannot inherit from itself"):
            role.set_parent_role(role.id)

    def test_system_role_modification_restrictions(self):
        """Test all restrictions on system role modifications."""
        system_role = Role.create(
            "System_Admin", "System administrator", self.creator_id, is_system_role=True
        )

        # Cannot deactivate system roles
        with pytest.raises(ValueError, match="Cannot deactivate system roles"):
            system_role.deactivate()

        # Cannot set parent for system roles
        parent_role = Role.create("Parent", "Parent role", self.creator_id, self.org_id)
        with pytest.raises(
            ValueError, match="System roles cannot inherit from other roles"
        ):
            system_role.set_parent_role(parent_role.id)

        # Cannot remove parent for system roles (even if they somehow had one)
        with pytest.raises(ValueError, match="System roles cannot be modified"):
            system_role.remove_parent_role()

        # Can check modification status
        can_modify, reason = system_role.can_be_modified()
        assert can_modify is False
        assert "System roles cannot be modified" in reason

        # Can check deletion status
        can_delete, reason = system_role.can_be_deleted()
        assert can_delete is False
        assert "System roles cannot be deleted" in reason

    def test_inactive_role_modification_restrictions(self):
        """Test that inactive roles cannot be modified."""
        role = Role.create("Test_Role", "Test role", self.creator_id, self.org_id)
        inactive_role = role.deactivate()

        can_modify, reason = inactive_role.can_be_modified()
        assert can_modify is False
        assert "Inactive roles cannot be modified" in reason

    def test_role_scope_hierarchy_validation(self):
        """Test role scope validation in inheritance hierarchies."""
        # Global parent role
        global_role = Role.create("Global_Role", "Global role", self.creator_id)

        # Organization child role (valid)
        org_role = Role.create(
            "Org_Role",
            "Organization role",
            self.creator_id,
            self.org_id,
            parent_role_id=global_role.id,
        )

        # Create complete hierarchy for validation
        all_roles = [global_role, org_role]

        # Organization role inheriting from global role should be valid
        is_valid, message = org_role.validate_inheritance_rules(all_roles)
        assert is_valid is True

        # Test invalid scenario: global role trying to inherit from org role
        invalid_global = Role.create(
            "Invalid_Global",
            "Global role with org parent",
            self.creator_id,
            organization_id=None,
            parent_role_id=org_role.id,
        )

        all_roles_invalid = [global_role, org_role, invalid_global]
        is_valid, message = invalid_global.validate_inheritance_rules(all_roles_invalid)
        assert is_valid is False
        assert "Global role cannot inherit from organization role" in message

    def test_cross_organization_inheritance_validation(self):
        """Test that roles from different organizations cannot inherit from each other."""
        org1_id = uuid4()
        org2_id = uuid4()

        org1_role = Role.create("Org1_Role", "Role in org 1", self.creator_id, org1_id)
        org2_role = Role.create(
            "Org2_Role",
            "Role in org 2",
            self.creator_id,
            org2_id,
            parent_role_id=org1_role.id,
        )

        all_roles = [org1_role, org2_role]
        is_valid, message = org2_role.validate_inheritance_rules(all_roles)
        assert is_valid is False
        assert "Child role must be in same organization as parent" in message

    def test_circular_inheritance_detection_complex(self):
        """Test circular inheritance detection in complex scenarios."""
        # Create roles A -> B -> C -> D
        role_a = Role.create("Role_A", "Role A", self.creator_id, self.org_id)
        role_b = Role.create(
            "Role_B", "Role B", self.creator_id, self.org_id, parent_role_id=role_a.id
        )
        role_c = Role.create(
            "Role_C", "Role C", self.creator_id, self.org_id, parent_role_id=role_b.id
        )
        role_d = Role.create(
            "Role_D", "Role D", self.creator_id, self.org_id, parent_role_id=role_c.id
        )

        all_roles = [role_a, role_b, role_c, role_d]

        # Verify D is descendant of A
        assert role_d.is_descendant_of(all_roles, role_a.id) is True

        # Try to make A inherit from D (creating a cycle)
        role_a_with_cycle = role_a.set_parent_role(role_d.id)
        roles_with_cycle = [role_a_with_cycle, role_b, role_c, role_d]

        is_valid, message = role_a_with_cycle.validate_inheritance_rules(
            roles_with_cycle
        )
        assert is_valid is False
        assert "Circular inheritance detected" in message

    def test_inheritance_path_with_disconnected_hierarchy(self):
        """Test inheritance path calculation with disconnected or broken hierarchies."""
        # Create roles with missing intermediate parent
        role_a = Role.create("Role_A", "Role A", self.creator_id, self.org_id)
        role_c = Role.create(
            "Role_C", "Role C", self.creator_id, self.org_id, parent_role_id=uuid4()
        )  # Missing parent

        # Should handle gracefully
        hierarchy_path = role_c.get_role_hierarchy_path([role_a, role_c])
        assert role_c.id in hierarchy_path

    def test_deep_inheritance_hierarchy_performance(self):
        """Test role hierarchy operations with deep inheritance chains."""
        # Create deep chain: 20 levels deep
        roles = []
        parent_id = None

        for i in range(20):
            role = Role.create(
                f"Deep_Role_{i}",
                f"Role at depth {i}",
                self.creator_id,
                self.org_id,
                parent_role_id=parent_id,
            )
            roles.append(role)
            parent_id = role.id

        deepest_role = roles[-1]

        # Test hierarchy path calculation
        hierarchy_path = deepest_role.get_role_hierarchy_path(roles)
        assert len(hierarchy_path) == 20
        assert hierarchy_path[0] == roles[0].id  # Root
        assert hierarchy_path[-1] == deepest_role.id  # Leaf

        # Test descendant check
        assert deepest_role.is_descendant_of(roles, roles[0].id) is True
        assert deepest_role.is_descendant_of(roles, roles[10].id) is True
        assert roles[0].is_descendant_of(roles, deepest_role.id) is False

    def test_role_inheritance_with_infinite_loop_protection(self):
        """Test that role hierarchy methods protect against infinite loops."""
        # Create roles with potential for infinite loops in broken hierarchy
        role_a = Role.create("Role_A", "Role A", self.creator_id, self.org_id)
        role_b = Role.create(
            "Role_B", "Role B", self.creator_id, self.org_id, parent_role_id=role_a.id
        )

        # Manually create a broken hierarchy by modifying parent references
        # (this simulates corrupted data)
        role_a_corrupted = role_a.model_copy(update={"parent_role_id": role_b.id})

        corrupted_roles = [role_a_corrupted, role_b]

        # Methods should handle this gracefully without infinite loops
        hierarchy_path = role_b.get_role_hierarchy_path(corrupted_roles)
        assert len(hierarchy_path) > 0  # Should return something, not loop forever

        # Descendant check should also handle loops
        is_descendant = role_b.is_descendant_of(corrupted_roles, role_a.id)
        # Should handle gracefully without hanging

    def test_role_hierarchy_validation_with_missing_roles(self):
        """Test hierarchy validation when some roles in the chain are missing."""
        role_a = Role.create("Role_A", "Role A", self.creator_id, self.org_id)
        # role_b is missing
        role_c = Role.create(
            "Role_C", "Role C", self.creator_id, self.org_id, parent_role_id=uuid4()
        )

        incomplete_hierarchy = [role_a, role_c]

        is_valid, message = role_c.validate_inheritance_rules(incomplete_hierarchy)
        assert is_valid is False
        assert "Parent role not found" in message

    def test_role_boundary_conditions(self):
        """Test role entity boundary conditions and edge cases."""
        # Test role with minimal valid data
        minimal_role = Role.create("Min", "M", self.creator_id)
        assert minimal_role.name.value == "min"
        assert minimal_role.is_global_role() is True
        assert minimal_role.is_organization_role() is False

        # Test role state transitions
        role = Role.create("Test", "Test role", self.creator_id, self.org_id)

        # Active -> Inactive -> Active
        inactive_role = role.deactivate()
        assert inactive_role.is_active is False
        assert inactive_role.updated_at is not None

        reactivated_role = inactive_role.activate()
        assert reactivated_role.is_active is True

        # Test description updates
        updated_role = role.update_description("New description")
        assert updated_role.description == "New description"
        assert updated_role.updated_at is not None

    def test_role_immutability_constraints(self):
        """Test that role objects are properly immutable."""
        role = Role.create(
            "Immutable_Role", "Test immutability", self.creator_id, self.org_id
        )

        # Should not be able to modify attributes directly
        with pytest.raises(ValidationError):
            role.name = RoleName(value="Modified")

        with pytest.raises(ValidationError):
            role.is_active = False

        with pytest.raises(ValidationError):
            role.parent_role_id = uuid4()

    def test_role_helper_method_edge_cases(self):
        """Test edge cases in role helper methods."""
        role = Role.create(
            "Helper_Test", "Test helper methods", self.creator_id, self.org_id
        )

        # Test with empty hierarchy
        assert role.get_role_hierarchy_path([]) == [role.id]
        assert role.is_descendant_of([], uuid4()) is False

        # Test with self in hierarchy but no parent
        assert role.get_role_hierarchy_path([role]) == [role.id]

        # Test descendant check with non-existent ancestor
        assert role.is_descendant_of([role], uuid4()) is False

    def test_role_organization_scope_edge_cases(self):
        """Test edge cases related to role organization scope."""
        # Global role
        global_role = Role.create("Global", "Global role", self.creator_id)
        assert global_role.is_global_role() is True
        assert global_role.is_organization_role() is False

        # Organization role
        org_role = Role.create("Org", "Org role", self.creator_id, self.org_id)
        assert org_role.is_global_role() is False
        assert org_role.is_organization_role() is True

        # Test scope validation in inheritance
        all_roles = [global_role, org_role]

        # Valid: org role inheriting from global
        org_inheriting_global = org_role.set_parent_role(global_role.id)
        is_valid, _ = org_inheriting_global.validate_inheritance_rules(
            all_roles + [org_inheriting_global]
        )
        assert is_valid is True

    def test_role_temporal_edge_cases(self):
        """Test edge cases related to role temporal properties."""
        role = Role.create(
            "Temporal_Test", "Test temporal properties", self.creator_id, self.org_id
        )

        # Test that creation time is set
        assert role.created_at is not None
        assert role.updated_at is None

        # Test that updates set update time
        updated_role = role.update_description("Updated")
        assert updated_role.updated_at is not None
        assert updated_role.updated_at.timestamp() > role.created_at.timestamp()

        # Test state changes set update time
        deactivated_role = role.deactivate()
        assert deactivated_role.updated_at is not None

    def test_role_validation_with_inactive_parent(self):
        """Test role validation when parent becomes inactive."""
        parent_role = Role.create("Parent", "Parent role", self.creator_id, self.org_id)
        child_role = Role.create(
            "Child",
            "Child role",
            self.creator_id,
            self.org_id,
            parent_role_id=parent_role.id,
        )

        # Initially valid
        all_roles = [parent_role, child_role]
        is_valid, _ = child_role.validate_inheritance_rules(all_roles)
        assert is_valid is True

        # Deactivate parent
        inactive_parent = parent_role.deactivate()
        all_roles_with_inactive = [inactive_parent, child_role]

        # Should now be invalid
        is_valid, message = child_role.validate_inheritance_rules(
            all_roles_with_inactive
        )
        assert is_valid is False
        assert "Cannot inherit from inactive role" in message

    def test_role_hierarchy_consistency_checks(self):
        """Test comprehensive role hierarchy consistency."""
        # Create complex hierarchy
        root = Role.create("Root", "Root role", self.creator_id, self.org_id)
        branch1 = Role.create(
            "Branch1", "Branch 1", self.creator_id, self.org_id, parent_role_id=root.id
        )
        branch2 = Role.create(
            "Branch2", "Branch 2", self.creator_id, self.org_id, parent_role_id=root.id
        )
        leaf1 = Role.create(
            "Leaf1", "Leaf 1", self.creator_id, self.org_id, parent_role_id=branch1.id
        )
        leaf2 = Role.create(
            "Leaf2", "Leaf 2", self.creator_id, self.org_id, parent_role_id=branch2.id
        )

        all_roles = [root, branch1, branch2, leaf1, leaf2]

        # Validate all roles
        for role in all_roles:
            is_valid, message = role.validate_inheritance_rules(all_roles)
            assert is_valid is True, (
                f"Role {role.name.value} validation failed: {message}"
            )

        # Test hierarchy paths
        assert leaf1.get_role_hierarchy_path(all_roles) == [
            root.id,
            branch1.id,
            leaf1.id,
        ]
        assert leaf2.get_role_hierarchy_path(all_roles) == [
            root.id,
            branch2.id,
            leaf2.id,
        ]

        # Test descendant relationships
        assert leaf1.is_descendant_of(all_roles, root.id) is True
        assert leaf1.is_descendant_of(all_roles, branch2.id) is False
        assert leaf2.is_descendant_of(all_roles, root.id) is True
        assert leaf2.is_descendant_of(all_roles, branch1.id) is False
