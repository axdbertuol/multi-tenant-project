import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4, UUID
from typing import List, Dict

from authorization.application.use_cases.role_use_cases import RoleUseCase
from authorization.application.dtos.role_dto import (
    RoleCreateDTO, 
    RoleUpdateDTO, 
    RoleResponseDTO,
    RoleInheritanceUpdateDTO
)
from authorization.domain.entities.role import Role
from src.authorization.domain.entities.permission import Permission, PermissionAction
from authorization.domain.services.role_inheritance_service import RoleInheritanceService


class TestRoleInheritanceUseCases:
    """Test cases for role inheritance functionality in use cases layer."""
    
    def setup_method(self):
        """Set up test fixtures with mocked dependencies."""
        self.mock_uow = Mock()
        self.mock_role_repository = Mock()
        self.mock_permission_repository = Mock()
        self.mock_role_permission_repository = Mock()
        
        def get_repository(name):
            if name == "role":
                return self.mock_role_repository
            elif name == "permission":
                return self.mock_permission_repository
            elif name == "role_permission":
                return self.mock_role_permission_repository
            return None
        
        self.mock_uow.get_repository.side_effect = get_repository
        self.mock_uow.__enter__ = Mock(return_value=self.mock_uow)
        self.mock_uow.__exit__ = Mock(return_value=None)
        
        self.use_case = RoleUseCase(self.mock_uow)
        self.creator_id = uuid4()
        self.org_id = uuid4()

    def test_create_role_inheriting_from_default_rh(self):
        """Test creating a new role that inherits from Default_RH."""
        # Setup Default_RH role
        default_rh_id = uuid4()
        default_rh = Role.create(
            "Default_RH",
            "Default HR role with common permissions",
            self.creator_id,
            self.org_id
        )
        default_rh = default_rh.model_copy(update={"id": default_rh_id})
        
        # Create DTO for enhanced role
        enhanced_rh_dto = RoleCreateDTO(
            name="Enhanced_RH",
            description="Enhanced HR role with additional permissions",
            organization_id=self.org_id,
            parent_role_id=default_rh_id
        )
        
        # Mock repository responses
        self.mock_role_repository.get_by_id.return_value = default_rh
        self.mock_role_repository.get_by_name_and_organization.return_value = None  # Name available
        self.mock_role_repository.get_all_in_organization.return_value = [default_rh]
        
        # Mock role creation
        created_role = Role.create(
            enhanced_rh_dto.name,
            enhanced_rh_dto.description,
            self.creator_id,
            enhanced_rh_dto.organization_id,
            parent_role_id=enhanced_rh_dto.parent_role_id
        )
        self.mock_role_repository.save.return_value = created_role
        
        # Execute use case
        result = self.use_case.create_role(enhanced_rh_dto, self.creator_id)
        
        # Verify result
        assert isinstance(result, RoleResponseDTO)
        assert result.name == "Enhanced_RH"
        assert result.parent_role_id == default_rh_id
        
        # Verify repository interactions
        self.mock_role_repository.get_by_id.assert_called_once_with(default_rh_id)
        self.mock_role_repository.save.assert_called_once()

    def test_create_role_with_invalid_parent_role(self):
        """Test creating role with non-existent parent role fails."""
        non_existent_parent_id = uuid4()
        
        dto = RoleCreateDTO(
            name="Invalid_Child",
            description="Role with invalid parent",
            organization_id=self.org_id,
            parent_role_id=non_existent_parent_id
        )
        
        # Mock parent role not found
        self.mock_role_repository.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Parent role not found"):
            self.use_case.create_role(dto, self.creator_id)

    def test_create_role_with_circular_inheritance(self):
        """Test prevention of circular inheritance in role creation."""
        # Setup existing roles: A -> B -> C
        role_a_id = uuid4()
        role_b_id = uuid4()
        role_c_id = uuid4()
        
        role_a = Role.create("Role_A", "Role A", self.creator_id, self.org_id)
        role_a = role_a.model_copy(update={"id": role_a_id})
        
        role_b = Role.create("Role_B", "Role B", self.creator_id, self.org_id, parent_role_id=role_a_id)
        role_b = role_b.model_copy(update={"id": role_b_id})
        
        role_c = Role.create("Role_C", "Role C", self.creator_id, self.org_id, parent_role_id=role_b_id)
        role_c = role_c.model_copy(update={"id": role_c_id})
        
        # Try to make role_a inherit from role_c (creating a cycle)
        dto = RoleCreateDTO(
            name="Circular_Role",
            description="Role that would create circular inheritance",
            organization_id=self.org_id,
            parent_role_id=role_c_id
        )
        
        # Mock repository responses
        self.mock_role_repository.get_by_id.return_value = role_c
        self.mock_role_repository.get_all_in_organization.return_value = [role_a, role_b, role_c]
        
        # Mock the inheritance service to detect circular dependency
        with patch.object(self.use_case, '_validate_inheritance_rules') as mock_validate:
            mock_validate.return_value = (False, "Would create circular inheritance")
            
            with pytest.raises(ValueError, match="circular inheritance"):
                self.use_case.create_role(dto, self.creator_id)

    def test_update_role_inheritance_relationship(self):
        """Test updating role inheritance relationships."""
        # Setup existing roles
        child_role_id = uuid4()
        old_parent_id = uuid4()
        new_parent_id = uuid4()
        
        child_role = Role.create(
            "Child_Role",
            "Child role",
            self.creator_id,
            self.org_id,
            parent_role_id=old_parent_id
        )
        child_role = child_role.model_copy(update={"id": child_role_id})
        
        old_parent = Role.create("Old_Parent", "Old parent", self.creator_id, self.org_id)
        old_parent = old_parent.model_copy(update={"id": old_parent_id})
        
        new_parent = Role.create("New_Parent", "New parent", self.creator_id, self.org_id)
        new_parent = new_parent.model_copy(update={"id": new_parent_id})
        
        # Create update DTO
        inheritance_dto = RoleInheritanceUpdateDTO(
            parent_role_id=new_parent_id
        )
        
        # Mock repository responses
        self.mock_role_repository.get_by_id.side_effect = lambda role_id: {
            child_role_id: child_role,
            new_parent_id: new_parent
        }.get(role_id)
        
        self.mock_role_repository.get_all_in_organization.return_value = [old_parent, new_parent, child_role]
        
        # Mock successful update
        updated_role = child_role.set_parent_role(new_parent_id)
        self.mock_role_repository.save.return_value = updated_role
        
        # Execute use case
        result = self.use_case.update_role_inheritance(child_role_id, inheritance_dto, self.creator_id)
        
        # Verify result
        assert result.parent_role_id == new_parent_id
        self.mock_role_repository.save.assert_called_once()

    def test_remove_role_inheritance(self):
        """Test removing role inheritance relationship."""
        role_id = uuid4()
        parent_id = uuid4()
        
        role_with_parent = Role.create(
            "Child_Role",
            "Role with parent",
            self.creator_id,
            self.org_id,
            parent_role_id=parent_id
        )
        role_with_parent = role_with_parent.model_copy(update={"id": role_id})
        
        # Create DTO to remove inheritance
        inheritance_dto = RoleInheritanceUpdateDTO(parent_role_id=None)
        
        # Mock repository responses
        self.mock_role_repository.get_by_id.return_value = role_with_parent
        
        # Mock successful removal
        updated_role = role_with_parent.remove_parent_role()
        self.mock_role_repository.save.return_value = updated_role
        
        # Execute use case
        result = self.use_case.update_role_inheritance(role_id, inheritance_dto, self.creator_id)
        
        # Verify inheritance removed
        assert result.parent_role_id is None
        self.mock_role_repository.save.assert_called_once()

    def test_get_role_with_inherited_permissions(self):
        """Test retrieving role with its full inherited permission set."""
        # Setup role hierarchy: Base -> Enhanced
        base_role_id = uuid4()
        enhanced_role_id = uuid4()
        
        base_role = Role.create("Base_Role", "Base role", self.creator_id, self.org_id)
        base_role = base_role.model_copy(update={"id": base_role_id})
        
        enhanced_role = Role.create(
            "Enhanced_Role",
            "Enhanced role",
            self.creator_id,
            self.org_id,
            parent_role_id=base_role_id
        )
        enhanced_role = enhanced_role.model_copy(update={"id": enhanced_role_id})
        
        # Setup permissions
        base_permissions = [
            Permission.create("base_perm1", "Base permission 1", PermissionAction.READ, "resource1"),
            Permission.create("base_perm2", "Base permission 2", PermissionAction.UPDATE, "resource2")
        ]
        
        enhanced_permissions = [
            Permission.create("enhanced_perm1", "Enhanced permission 1", PermissionAction.DELETE, "resource3")
        ]
        
        # Mock repository responses
        self.mock_role_repository.get_by_id.return_value = enhanced_role
        self.mock_role_repository.get_all_in_organization.return_value = [base_role, enhanced_role]
        self.mock_role_permission_repository.get_permissions_for_role.side_effect = lambda role_id: {
            base_role_id: base_permissions,
            enhanced_role_id: enhanced_permissions
        }.get(role_id, [])
        
        # Execute use case
        result = self.use_case.get_role_with_permissions(enhanced_role_id)
        
        # Verify result includes inherited permissions
        assert result.id == enhanced_role_id
        assert len(result.permissions) == 3  # 2 from base + 1 from enhanced
        
        permission_names = [p.name for p in result.permissions]
        assert "base_perm1" in permission_names
        assert "base_perm2" in permission_names
        assert "enhanced_perm1" in permission_names

    def test_get_role_hierarchy_tree(self):
        """Test retrieving complete role hierarchy tree."""
        # Setup multi-level hierarchy
        root_id = uuid4()
        child1_id = uuid4()
        child2_id = uuid4()
        grandchild_id = uuid4()
        
        root_role = Role.create("Root", "Root role", self.creator_id, self.org_id)
        root_role = root_role.model_copy(update={"id": root_id})
        
        child1_role = Role.create("Child1", "Child 1", self.creator_id, self.org_id, parent_role_id=root_id)
        child1_role = child1_role.model_copy(update={"id": child1_id})
        
        child2_role = Role.create("Child2", "Child 2", self.creator_id, self.org_id, parent_role_id=root_id)
        child2_role = child2_role.model_copy(update={"id": child2_id})
        
        grandchild_role = Role.create("Grandchild", "Grandchild", self.creator_id, self.org_id, parent_role_id=child1_id)
        grandchild_role = grandchild_role.model_copy(update={"id": grandchild_id})
        
        all_roles = [root_role, child1_role, child2_role, grandchild_role]
        
        # Mock repository response
        self.mock_role_repository.get_all_in_organization.return_value = all_roles
        
        # Execute use case
        result = self.use_case.get_role_hierarchy_tree(self.org_id)
        
        # Verify tree structure
        assert len(result) > 0
        
        # Find root in result
        root_in_result = next((r for r in result if r.id == root_id), None)
        assert root_in_result is not None
        
        # Verify repository call
        self.mock_role_repository.get_all_in_organization.assert_called_once_with(self.org_id)

    def test_validate_role_inheritance_rules(self):
        """Test role inheritance validation."""
        # Setup invalid inheritance scenario
        system_role_id = uuid4()
        regular_role_id = uuid4()
        
        system_role = Role.create("System_Role", "System role", self.creator_id, is_system_role=True)
        system_role = system_role.model_copy(update={"id": system_role_id})
        
        regular_role = Role.create("Regular_Role", "Regular role", self.creator_id, self.org_id)
        regular_role = regular_role.model_copy(update={"id": regular_role_id})
        
        # Mock repository responses
        self.mock_role_repository.get_by_id.side_effect = lambda role_id: {
            system_role_id: system_role,
            regular_role_id: regular_role
        }.get(role_id)
        
        self.mock_role_repository.get_all_in_organization.return_value = [regular_role]
        
        # Test validation fails for system role inheritance
        is_valid, message = self.use_case.validate_role_inheritance(
            regular_role_id, system_role_id, self.org_id
        )
        
        assert is_valid is False
        assert "System roles cannot inherit" in message or "system" in message.lower()

    def test_delete_role_with_children_prevention(self):
        """Test that roles with child roles cannot be deleted."""
        parent_id = uuid4()
        child_id = uuid4()
        
        parent_role = Role.create("Parent_Role", "Parent role", self.creator_id, self.org_id)
        parent_role = parent_role.model_copy(update={"id": parent_id})
        
        child_role = Role.create("Child_Role", "Child role", self.creator_id, self.org_id, parent_role_id=parent_id)
        child_role = child_role.model_copy(update={"id": child_id})
        
        # Mock repository responses
        self.mock_role_repository.get_by_id.return_value = parent_role
        self.mock_role_repository.get_children_roles.return_value = [child_role]
        
        # Attempt to delete parent role
        with pytest.raises(ValueError, match="cannot be deleted.*child roles"):
            self.use_case.delete_role(parent_id, self.creator_id)

    def test_role_permission_inheritance_calculation_edge_cases(self):
        """Test edge cases in permission inheritance calculation."""
        # Setup scenario with permission conflicts/duplicates
        parent_id = uuid4()
        child_id = uuid4()
        
        parent_role = Role.create("Parent", "Parent role", self.creator_id, self.org_id)
        parent_role = parent_role.model_copy(update={"id": parent_id})
        
        child_role = Role.create("Child", "Child role", self.creator_id, self.org_id, parent_role_id=parent_id)
        child_role = child_role.model_copy(update={"id": child_id})
        
        # Create overlapping permissions
        parent_permissions = [
            Permission.create("read_data", "Read data", PermissionAction.READ, "data"),
            Permission.create("write_logs", "Write logs", PermissionAction.CREATE, "logs")
        ]
        
        child_permissions = [
            Permission.create("read_data_enhanced", "Enhanced read data", PermissionAction.READ, "data"),  # Same resource
            Permission.create("delete_data", "Delete data", PermissionAction.DELETE, "data")
        ]
        
        # Mock repository responses
        self.mock_role_repository.get_by_id.return_value = child_role
        self.mock_role_repository.get_all_in_organization.return_value = [parent_role, child_role]
        self.mock_role_permission_repository.get_permissions_for_role.side_effect = lambda role_id: {
            parent_id: parent_permissions,
            child_id: child_permissions
        }.get(role_id, [])
        
        # Execute use case
        result = self.use_case.get_role_with_permissions(child_id)
        
        # Verify no duplicates and proper inheritance
        data_permissions = [p for p in result.permissions if p.resource_type == "data"]
        
        # Should have permissions for data resource but without exact duplicates
        assert len(data_permissions) >= 2  # At least read and delete
        
        # Should have inherited non-conflicting permissions
        permission_names = [p.name for p in result.permissions]
        assert "write_logs" in permission_names  # Inherited from parent

    def test_bulk_role_inheritance_operations(self):
        """Test bulk operations on role inheritance."""
        # Setup multiple roles for bulk operations
        roles_data = []
        for i in range(5):
            role = Role.create(f"Role_{i}", f"Role {i}", self.creator_id, self.org_id)
            role = role.model_copy(update={"id": uuid4()})
            roles_data.append(role)
        
        # Mock repository responses
        self.mock_role_repository.get_all_in_organization.return_value = roles_data
        
        # Execute bulk validation
        validation_results = self.use_case.bulk_validate_role_hierarchy(self.org_id)
        
        # Verify results structure
        assert isinstance(validation_results, dict)
        assert "valid_roles" in validation_results
        assert "invalid_roles" in validation_results
        assert "errors" in validation_results
        
        # All roles should be valid in this simple case
        assert len(validation_results["invalid_roles"]) == 0

    def test_role_inheritance_performance_optimization(self):
        """Test that role inheritance operations are optimized for performance."""
        # Create large role hierarchy
        large_hierarchy = []
        for i in range(100):
            parent_id = large_hierarchy[-1].id if large_hierarchy else None
            role = Role.create(f"Role_{i}", f"Role {i}", self.creator_id, self.org_id, parent_role_id=parent_id)
            role = role.model_copy(update={"id": uuid4()})
            large_hierarchy.append(role)
        
        # Mock repository to return large hierarchy
        self.mock_role_repository.get_all_in_organization.return_value = large_hierarchy
        
        # Test that operations complete without timeout/performance issues
        deepest_role = large_hierarchy[-1]
        self.mock_role_repository.get_by_id.return_value = deepest_role
        self.mock_role_permission_repository.get_permissions_for_role.return_value = []
        
        # This should complete quickly even with deep hierarchy
        result = self.use_case.get_role_with_permissions(deepest_role.id)
        
        assert result.id == deepest_role.id
        
        # Verify repository was called efficiently (should not make excessive calls)
        assert self.mock_role_repository.get_all_in_organization.call_count <= 2