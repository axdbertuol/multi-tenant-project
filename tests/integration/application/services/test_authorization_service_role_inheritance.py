import pytest
from uuid import uuid4
from unittest.mock import Mock

from src.authorization.domain.entities.authorization_context import AuthorizationContext
from src.authorization.domain.entities.role import Role
from src.authorization.domain.entities.permission import Permission
from src.authorization.domain.services.authorization_service import AuthorizationService
from src.authorization.domain.services.rbac_service import RBACService
from src.authorization.domain.services.abac_service import ABACService
from src.authorization.domain.services.role_inheritance_service import RoleInheritanceService
from src.authorization.domain.value_objects.authorization_decision import DecisionResult


class TestAuthorizationServiceRoleInheritance:
    """Integration tests for AuthorizationService with role inheritance."""

    @pytest.fixture
    def mock_repositories(self):
        """Create all mock repositories."""
        return {
            'role_repo': Mock(),
            'permission_repo': Mock(),
            'role_permission_repo': Mock(),
            'policy_repo': Mock(),
            'resource_repo': Mock(),
        }

    @pytest.fixture
    def mock_policy_evaluation_service(self):
        """Create mock policy evaluation service."""
        return Mock()

    @pytest.fixture
    def role_inheritance_service(self):
        """Create role inheritance service."""
        return RoleInheritanceService()

    @pytest.fixture
    def authorization_service(self, mock_repositories, mock_policy_evaluation_service):
        """Create AuthorizationService with role inheritance support."""
        # Create enhanced RBAC service that uses role inheritance
        rbac_service = RBACService(
            mock_repositories['role_repo'],
            mock_repositories['permission_repo'],
            mock_repositories['role_permission_repo']
        )
        
        abac_service = ABACService(
            mock_repositories['policy_repo'],
            mock_repositories['resource_repo'],
            mock_policy_evaluation_service
        )
        
        return AuthorizationService(rbac_service, abac_service)

    @pytest.fixture
    def organization_id(self):
        """Sample organization ID."""
        return uuid4()

    @pytest.fixture
    def user_id(self):
        """Sample user ID."""
        return uuid4()

    def test_authorize_with_inherited_permissions_rh_example(
        self, 
        authorization_service, 
        mock_repositories, 
        organization_id,
        user_id
    ):
        """Test authorization with RH assistant -> RH manager inheritance."""
        # Arrange - Create role hierarchy: rh_assistente -> rh_gerente
        rh_assistente = Role.create(
            name="rh_assistente",
            description="HR Assistant with basic permissions",
            created_by=uuid4(),
            organization_id=organization_id
        )
        
        rh_gerente = Role.create(
            name="rh_gerente", 
            description="HR Manager with inherited permissions",
            created_by=uuid4(),
            organization_id=organization_id,
            parent_role_id=rh_assistente.id
        )

        # Create permissions for assistant role
        read_users_perm = Permission.create(
            name="read_users",
            description="Read user data",
            permission_type="read",
            resource_type="user"
        )
        
        read_reports_perm = Permission.create(
            name="read_reports",
            description="Read reports",
            permission_type="read", 
            resource_type="report"
        )
        
        # Create additional permissions for manager role
        manage_users_perm = Permission.create(
            name="manage_users",
            description="Manage users",
            permission_type="manage",
            resource_type="user"
        )
        
        approve_requests_perm = Permission.create(
            name="approve_requests",
            description="Approve requests",
            permission_type="approve",
            resource_type="request"
        )

        # Mock user has the manager role
        mock_repositories['role_repo'].get_user_roles.return_value = [rh_gerente]
        
        # Mock role hierarchy
        mock_repositories['role_repo'].get_role_hierarchy.return_value = [rh_assistente, rh_gerente]
        
        # Mock permissions per role
        def get_role_permissions(role_id):
            if role_id == rh_assistente.id:
                return [read_users_perm, read_reports_perm]
            elif role_id == rh_gerente.id:
                return [manage_users_perm, approve_requests_perm]
            return []
        
        mock_repositories['permission_repo'].get_role_permissions.side_effect = get_role_permissions
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        # Test inherited permission (from assistant role)
        context = AuthorizationContext.create(
            user_id=user_id,
            resource_type="user",
            action="read",  # This permission comes from parent role
            organization_id=organization_id
        )

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_allowed()
        assert decision.result == DecisionResult.ALLOW
        assert any(reason.type == "rbac_allow" for reason in decision.reasons)

    def test_authorize_with_deep_inheritance_hierarchy(
        self, 
        authorization_service, 
        mock_repositories, 
        organization_id,
        user_id
    ):
        """Test authorization with 3-level inheritance: employee -> supervisor -> manager."""
        # Arrange - Create 3-level hierarchy
        employee = Role.create(
            name="employee",
            description="Basic employee",
            created_by=uuid4(),
            organization_id=organization_id
        )
        
        supervisor = Role.create(
            name="supervisor",
            description="Supervisor with additional permissions",
            created_by=uuid4(),
            organization_id=organization_id,
            parent_role_id=employee.id
        )
        
        manager = Role.create(
            name="manager",
            description="Manager with full permissions", 
            created_by=uuid4(),
            organization_id=organization_id,
            parent_role_id=supervisor.id
        )

        # Create permissions for each level
        basic_perm = Permission.create("basic_access", "Basic access", "read", "document")
        supervisor_perm = Permission.create("supervisor_access", "Supervisor access", "write", "document")
        manager_perm = Permission.create("manager_access", "Manager access", "delete", "document")

        # User has manager role (should inherit all permissions)
        mock_repositories['role_repo'].get_user_roles.return_value = [manager]
        mock_repositories['role_repo'].get_role_hierarchy.return_value = [employee, supervisor, manager]
        
        def get_role_permissions(role_id):
            if role_id == employee.id:
                return [basic_perm]
            elif role_id == supervisor.id:
                return [supervisor_perm]
            elif role_id == manager.id:
                return [manager_perm]
            return []
        
        mock_repositories['permission_repo'].get_role_permissions.side_effect = get_role_permissions
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        # Test access to permission from grandparent role
        context = AuthorizationContext.create(
            user_id=user_id,
            resource_type="document",
            action="read",  # From employee role (2 levels up)
            organization_id=organization_id
        )

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_allowed()
        assert decision.result == DecisionResult.ALLOW

    def test_authorize_with_broken_inheritance_chain(
        self, 
        authorization_service, 
        mock_repositories, 
        organization_id,
        user_id
    ):
        """Test authorization when inheritance chain is broken (parent role missing)."""
        # Arrange - Child role references non-existent parent
        orphaned_role = Role.create(
            name="orphaned_role",
            description="Role with missing parent",
            created_by=uuid4(),
            organization_id=organization_id,
            parent_role_id=uuid4()  # Non-existent parent ID
        )
        
        orphaned_perm = Permission.create("orphaned_access", "Orphaned access", "read", "document")

        mock_repositories['role_repo'].get_user_roles.return_value = [orphaned_role]
        mock_repositories['role_repo'].get_role_hierarchy.return_value = [orphaned_role]  # Only child, no parent
        mock_repositories['permission_repo'].get_role_permissions.return_value = [orphaned_perm]
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        context = AuthorizationContext.create(
            user_id=user_id,
            resource_type="document",
            action="read",
            organization_id=organization_id
        )

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        # Should still work with just the child role's permissions
        assert decision.is_allowed()
        assert decision.result == DecisionResult.ALLOW

    def test_authorize_with_inactive_parent_role(
        self, 
        authorization_service, 
        mock_repositories, 
        organization_id,
        user_id
    ):
        """Test authorization when parent role is inactive."""
        # Arrange
        parent_role = Role.create(
            name="parent_role",
            description="Inactive parent role",
            created_by=uuid4(),
            organization_id=organization_id
        )
        parent_role = parent_role.deactivate()  # Make parent inactive
        
        child_role = Role.create(
            name="child_role",
            description="Active child role",
            created_by=uuid4(),
            organization_id=organization_id,
            parent_role_id=parent_role.id
        )

        parent_perm = Permission.create("parent_access", "Parent access", "write", "document")
        child_perm = Permission.create("child_access", "Child access", "read", "document")

        mock_repositories['role_repo'].get_user_roles.return_value = [child_role]
        mock_repositories['role_repo'].get_role_hierarchy.return_value = [parent_role, child_role]
        
        def get_role_permissions(role_id):
            if role_id == parent_role.id:
                return [parent_perm]
            elif role_id == child_role.id:
                return [child_perm]
            return []
        
        mock_repositories['permission_repo'].get_role_permissions.side_effect = get_role_permissions
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        # Test access to parent permission (should be denied since parent is inactive)
        context = AuthorizationContext.create(
            user_id=user_id,
            resource_type="document",
            action="write",  # Parent's permission
            organization_id=organization_id
        )

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_denied()  # Should not inherit from inactive parent

        # Test access to child permission (should work)
        context = AuthorizationContext.create(
            user_id=user_id,
            resource_type="document", 
            action="read",  # Child's permission
            organization_id=organization_id
        )

        decision = authorization_service.authorize(context)
        assert decision.is_allowed()  # Child's own permissions should work

    def test_authorize_with_circular_inheritance_prevention(
        self, 
        authorization_service, 
        mock_repositories, 
        organization_id,
        user_id
    ):
        """Test that circular inheritance doesn't cause infinite loops."""
        # Arrange - Create potential circular reference
        role_a = Role.create(
            name="role_a",
            description="Role A",
            created_by=uuid4(),
            organization_id=organization_id
        )
        
        role_b = Role.create(
            name="role_b", 
            description="Role B",
            created_by=uuid4(),
            organization_id=organization_id,
            parent_role_id=role_a.id
        )
        
        # Simulate circular reference (this should be prevented by domain logic)
        role_a_with_parent = role_a.model_copy(update={"parent_role_id": role_b.id})

        perm_a = Permission.create("access_a", "Access A", "read", "resource_a")
        perm_b = Permission.create("access_b", "Access B", "read", "resource_b")

        mock_repositories['role_repo'].get_user_roles.return_value = [role_b]
        mock_repositories['role_repo'].get_role_hierarchy.return_value = [role_a_with_parent, role_b]
        
        def get_role_permissions(role_id):
            if role_id == role_a.id:
                return [perm_a]
            elif role_id == role_b.id:
                return [perm_b]
            return []
        
        mock_repositories['permission_repo'].get_role_permissions.side_effect = get_role_permissions
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        context = AuthorizationContext.create(
            user_id=user_id,
            resource_type="resource_a",
            action="read",
            organization_id=organization_id
        )

        # Act & Assert
        # Should not hang or crash due to circular reference
        decision = authorization_service.authorize(context)
        
        # The exact result depends on how the inheritance service handles cycles
        # but it should complete in reasonable time
        assert decision.result in [DecisionResult.ALLOW, DecisionResult.DENY]

    def test_authorize_with_multiple_inheritance_paths(
        self, 
        authorization_service, 
        mock_repositories, 
        organization_id,
        user_id
    ):
        """Test authorization with user having multiple roles with different inheritance."""
        # Arrange - User has multiple roles with different inheritance chains
        base_role = Role.create(
            name="base_role",
            description="Base role",
            created_by=uuid4(),
            organization_id=organization_id
        )
        
        admin_role = Role.create(
            name="admin_role",
            description="Admin role inheriting from base",
            created_by=uuid4(),
            organization_id=organization_id,
            parent_role_id=base_role.id
        )
        
        special_role = Role.create(
            name="special_role",
            description="Special role with no inheritance",
            created_by=uuid4(),
            organization_id=organization_id
        )

        base_perm = Permission.create("base_access", "Base access", "read", "document")
        admin_perm = Permission.create("admin_access", "Admin access", "write", "document")
        special_perm = Permission.create("special_access", "Special access", "execute", "system")

        # User has both admin and special roles
        mock_repositories['role_repo'].get_user_roles.return_value = [admin_role, special_role]
        mock_repositories['role_repo'].get_role_hierarchy.return_value = [base_role, admin_role, special_role]
        
        def get_role_permissions(role_id):
            if role_id == base_role.id:
                return [base_perm]
            elif role_id == admin_role.id:
                return [admin_perm]
            elif role_id == special_role.id:
                return [special_perm]
            return []
        
        mock_repositories['permission_repo'].get_role_permissions.side_effect = get_role_permissions
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        # Test access to inherited permission
        context = AuthorizationContext.create(
            user_id=user_id,
            resource_type="document",
            action="read",  # From base role via admin inheritance
            organization_id=organization_id
        )

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_allowed()
        assert decision.result == DecisionResult.ALLOW

        # Test access to special role permission
        context = AuthorizationContext.create(
            user_id=user_id,
            resource_type="system",
            action="execute",  # From special role (no inheritance)
            organization_id=organization_id
        )

        decision = authorization_service.authorize(context)
        assert decision.is_allowed()

    def test_authorize_inheritance_performance_with_many_levels(
        self, 
        authorization_service, 
        mock_repositories, 
        organization_id,
        user_id
    ):
        """Test performance with deep inheritance hierarchy (10 levels)."""
        # Arrange - Create 10-level inheritance chain
        roles = []
        permissions = []
        
        # Create root role
        root_role = Role.create(
            name="level_0",
            description="Root level role",
            created_by=uuid4(),
            organization_id=organization_id
        )
        roles.append(root_role)
        
        root_perm = Permission.create("access_0", "Level 0 access", "read", "level_0")
        permissions.append(root_perm)
        
        # Create 9 additional levels
        for i in range(1, 10):
            role = Role.create(
                name=f"level_{i}",
                description=f"Level {i} role",
                created_by=uuid4(),
                organization_id=organization_id,
                parent_role_id=roles[i-1].id
            )
            roles.append(role)
            
            perm = Permission.create(f"access_{i}", f"Level {i} access", "read", f"level_{i}")
            permissions.append(perm)

        # User has the deepest role (level 9)
        mock_repositories['role_repo'].get_user_roles.return_value = [roles[-1]]
        mock_repositories['role_repo'].get_role_hierarchy.return_value = roles
        
        def get_role_permissions(role_id):
            for i, role in enumerate(roles):
                if role.id == role_id:
                    return [permissions[i]]
            return []
        
        mock_repositories['permission_repo'].get_role_permissions.side_effect = get_role_permissions
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        # Test access to root permission (9 levels up)
        context = AuthorizationContext.create(
            user_id=user_id,
            resource_type="level_0",
            action="read",
            organization_id=organization_id
        )

        # Act
        start_time = authorization_service.authorize(context).evaluation_time_ms

        # Assert
        # Should complete in reasonable time (< 100ms for deep hierarchy)
        assert start_time < 100
        
        decision = authorization_service.authorize(context)
        assert decision.is_allowed()  # Should inherit from root