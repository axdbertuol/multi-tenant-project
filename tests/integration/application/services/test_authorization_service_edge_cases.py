import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock, patch

from src.authorization.domain.entities.authorization_context import AuthorizationContext
from src.authorization.domain.entities.role import Role
from src.authorization.domain.entities.permission import Permission
from src.authorization.domain.entities.policy import Policy
from src.authorization.domain.services.authorization_service import AuthorizationService
from src.authorization.domain.services.rbac_service import RBACService
from src.authorization.domain.services.abac_service import ABACService
from src.authorization.domain.services.policy_evaluation_service import PolicyEvaluationService
from src.authorization.domain.value_objects.authorization_decision import DecisionResult


class TestAuthorizationServiceEdgeCases:
    """Edge case tests for AuthorizationService authorize function."""

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
        return Mock(spec=PolicyEvaluationService)

    @pytest.fixture
    def authorization_service(self, mock_repositories, mock_policy_evaluation_service):
        """Create AuthorizationService with all mocks."""
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
    def sample_context(self):
        """Create a sample authorization context."""
        return AuthorizationContext.create(
            user_id=uuid4(),
            resource_type="document",
            action="read",
            organization_id=uuid4()
        )

    def test_authorize_with_inactive_roles(
        self, 
        authorization_service, 
        mock_repositories, 
        sample_context
    ):
        """Test authorization when user has inactive roles."""
        # Arrange
        inactive_role = Role.create(
            name="inactive_admin",
            description="Inactive admin role",
            created_by=uuid4(),
            organization_id=sample_context.organization_id
        )
        inactive_role = inactive_role.deactivate()
        
        mock_repositories['role_repo'].get_user_roles.return_value = [inactive_role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = []
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        # Act
        decision = authorization_service.authorize(sample_context)

        # Assert
        assert decision.is_denied()
        # Should treat inactive roles as if user has no permissions

    def test_authorize_with_inactive_permissions(
        self, 
        authorization_service, 
        mock_repositories, 
        sample_context
    ):
        """Test authorization when role has inactive permissions."""
        # Arrange
        active_role = Role.create(
            name="admin",
            description="Admin role",
            created_by=uuid4(),
            organization_id=sample_context.organization_id
        )
        
        inactive_permission = Permission.create(
            name="read_documents",
            description="Read documents",
            permission_type="read",
            resource_type="document"
        )
        inactive_permission = inactive_permission.deactivate()
        
        mock_repositories['role_repo'].get_user_roles.return_value = [active_role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = [inactive_permission]
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        # Act
        decision = authorization_service.authorize(sample_context)

        # Assert
        assert decision.is_denied()
        assert any(reason.type == "rbac_no_permissions" for reason in decision.reasons)

    def test_authorize_with_inactive_policies(
        self, 
        authorization_service, 
        mock_repositories, 
        mock_policy_evaluation_service,
        sample_context
    ):
        """Test authorization when policies are inactive."""
        # Arrange
        # RBAC denies
        role = Role.create("user", "User role", uuid4(), sample_context.organization_id)
        mock_repositories['role_repo'].get_user_roles.return_value = [role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = []
        
        # ABAC has inactive policy
        inactive_policy = Policy.create(
            name="inactive_policy",
            description="Inactive policy",
            effect="allow",
            resource_type="document",
            action="read",
            conditions=[],
            organization_id=sample_context.organization_id,
            created_by=uuid4()
        )
        inactive_policy = inactive_policy.deactivate()
        
        mock_repositories['policy_repo'].get_applicable_policies.return_value = [inactive_policy]

        # Act
        decision = authorization_service.authorize(sample_context)

        # Assert
        assert decision.is_denied()
        # Inactive policies should not be evaluated
        mock_policy_evaluation_service.evaluate_policy.assert_not_called()

    def test_authorize_with_none_resource_id(
        self, 
        authorization_service, 
        mock_repositories, 
        mock_policy_evaluation_service
    ):
        """Test authorization when resource_id is None."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=uuid4(),
            resource_type="document",
            action="read",
            organization_id=uuid4(),
            resource_id=None  # No specific resource
        )
        
        role = Role.create("admin", "Admin", uuid4(), context.organization_id)
        permission = Permission.create("read_documents", "Read docs", "read", "document")
        
        mock_repositories['role_repo'].get_user_roles.return_value = [role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = [permission]
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_allowed()
        # Resource repository should not be called when resource_id is None
        mock_repositories['resource_repo'].get_by_resource_id.assert_not_called()

    def test_authorize_with_none_organization_id(
        self, 
        authorization_service, 
        mock_repositories
    ):
        """Test authorization when organization_id is None (global context)."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=uuid4(),
            resource_type="system",
            action="admin",
            organization_id=None  # Global context
        )
        
        # Global system role
        system_role = Role.create(
            name="system_admin",
            description="System admin",
            created_by=uuid4(),
            organization_id=None,  # Global role
            is_system_role=True
        )
        
        system_permission = Permission.create(
            name="admin_system",
            description="Admin system",
            permission_type="admin",
            resource_type="system"
        )
        
        mock_repositories['role_repo'].get_user_roles.return_value = [system_role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = [system_permission]
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_allowed()
        # Should work with global context
        mock_repositories['role_repo'].get_user_roles.assert_called_with(context.user_id, None)

    def test_authorize_with_extremely_long_evaluation_time(
        self, 
        authorization_service, 
        mock_repositories, 
        mock_policy_evaluation_service,
        sample_context
    ):
        """Test authorization with policies that take a long time to evaluate."""
        # Arrange
        role = Role.create("user", "User", uuid4(), sample_context.organization_id)
        mock_repositories['role_repo'].get_user_roles.return_value = [role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = []
        
        policy = Policy.create(
            name="slow_policy",
            description="Slow policy",
            effect="allow",
            resource_type="document",
            action="read",
            conditions=[],
            organization_id=sample_context.organization_id,
            created_by=uuid4()
        )
        mock_repositories['policy_repo'].get_applicable_policies.return_value = [policy]
        
        # Simulate slow policy evaluation
        def slow_evaluation(*args):
            import time
            time.sleep(0.1)  # 100ms delay
            return True
            
        mock_policy_evaluation_service.evaluate_policy.side_effect = slow_evaluation

        # Act
        decision = authorization_service.authorize(sample_context)

        # Assert
        assert decision.is_allowed()
        assert decision.evaluation_time_ms >= 100  # Should track the delay

    def test_authorize_with_empty_conditions_policy(
        self, 
        authorization_service, 
        mock_repositories, 
        mock_policy_evaluation_service,
        sample_context
    ):
        """Test authorization with policy that has empty conditions."""
        # Arrange
        # RBAC denies
        role = Role.create("user", "User", uuid4(), sample_context.organization_id)
        mock_repositories['role_repo'].get_user_roles.return_value = [role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = []
        
        # ABAC has policy with empty conditions (should always apply)
        always_allow_policy = Policy.create(
            name="always_allow",
            description="Always allow",
            effect="allow",
            resource_type="document",
            action="read",
            conditions=[],  # Empty conditions
            organization_id=sample_context.organization_id,
            created_by=uuid4()
        )
        
        mock_repositories['policy_repo'].get_applicable_policies.return_value = [always_allow_policy]
        mock_policy_evaluation_service.evaluate_policy.return_value = True

        # Act
        decision = authorization_service.authorize(sample_context)

        # Assert
        assert decision.is_allowed()

    def test_authorize_with_conflicting_policy_priorities(
        self, 
        authorization_service, 
        mock_repositories, 
        mock_policy_evaluation_service,
        sample_context
    ):
        """Test authorization with multiple policies having different priorities."""
        # Arrange
        role = Role.create("admin", "Admin", uuid4(), sample_context.organization_id)
        permission = Permission.create("read_documents", "Read docs", "read", "document")
        
        mock_repositories['role_repo'].get_user_roles.return_value = [role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = [permission]
        
        # Multiple policies with different priorities
        low_priority_deny = Policy.create(
            name="low_deny",
            description="Low priority deny",
            effect="deny",
            resource_type="document",
            action="read",
            conditions=[],
            organization_id=sample_context.organization_id,
            created_by=uuid4(),
            priority=1  # Low priority
        )
        
        high_priority_allow = Policy.create(
            name="high_allow",
            description="High priority allow",
            effect="allow",
            resource_type="document",
            action="read",
            conditions=[],
            organization_id=sample_context.organization_id,
            created_by=uuid4(),
            priority=100  # High priority
        )
        
        mock_repositories['policy_repo'].get_applicable_policies.return_value = [
            low_priority_deny, high_priority_allow
        ]
        mock_policy_evaluation_service.evaluate_policy.return_value = True

        # Act
        decision = authorization_service.authorize(sample_context)

        # Assert
        assert decision.is_denied()  # Deny should still override regardless of priority

    def test_authorize_with_policy_evaluation_returning_none(
        self, 
        authorization_service, 
        mock_repositories, 
        mock_policy_evaluation_service,
        sample_context
    ):
        """Test authorization when policy evaluation returns None (not applicable)."""
        # Arrange
        role = Role.create("user", "User", uuid4(), sample_context.organization_id)
        mock_repositories['role_repo'].get_user_roles.return_value = [role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = []
        
        policy = Policy.create(
            name="conditional_policy",
            description="Conditional policy",
            effect="allow",
            resource_type="document",
            action="read",
            conditions=[{"user.department": "engineering"}],
            organization_id=sample_context.organization_id,
            created_by=uuid4()
        )
        
        mock_repositories['policy_repo'].get_applicable_policies.return_value = [policy]
        mock_policy_evaluation_service.evaluate_policy.return_value = None  # Not applicable

        # Act
        decision = authorization_service.authorize(sample_context)

        # Assert
        assert decision.is_denied()
        assert any(reason.type == "abac_not_applicable" for reason in decision.reasons)

    def test_authorize_with_malformed_context_attributes(
        self, 
        authorization_service, 
        mock_repositories
    ):
        """Test authorization with malformed context attributes."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=uuid4(),
            resource_type="document",
            action="read",
            organization_id=uuid4(),
            user_attributes={"invalid": object()},  # Non-serializable object
            resource_attributes={"nested": {"deep": {"value": 123}}},  # Deeply nested
            environment_attributes={"null_value": None}  # Null value
        )
        
        role = Role.create("user", "User", uuid4(), context.organization_id)
        mock_repositories['role_repo'].get_user_roles.return_value = [role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = []
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        # Act & Assert
        # Should not raise exception even with malformed attributes
        decision = authorization_service.authorize(context)
        assert decision.is_denied()

    def test_authorize_with_recursive_policy_references(
        self, 
        authorization_service, 
        mock_repositories, 
        mock_policy_evaluation_service,
        sample_context
    ):
        """Test authorization with policies that might have circular references."""
        # Arrange
        role = Role.create("user", "User", uuid4(), sample_context.organization_id)
        mock_repositories['role_repo'].get_user_roles.return_value = [role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = []
        
        # Policy with potentially recursive condition
        recursive_policy = Policy.create(
            name="recursive_policy",
            description="Recursive policy",
            effect="allow",
            resource_type="document",
            action="read",
            conditions=[{"user.id": "{{user.id}}"}],  # Self-reference
            organization_id=sample_context.organization_id,
            created_by=uuid4()
        )
        
        mock_repositories['policy_repo'].get_applicable_policies.return_value = [recursive_policy]
        mock_policy_evaluation_service.evaluate_policy.return_value = True

        # Act
        decision = authorization_service.authorize(sample_context)

        # Assert
        assert decision.is_allowed()
        # Should handle self-references gracefully

    def test_authorize_with_extremely_large_number_of_policies(
        self, 
        authorization_service, 
        mock_repositories, 
        mock_policy_evaluation_service,
        sample_context
    ):
        """Test authorization with a large number of policies."""
        # Arrange
        role = Role.create("user", "User", uuid4(), sample_context.organization_id)
        mock_repositories['role_repo'].get_user_roles.return_value = [role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = []
        
        # Create 100 policies
        policies = []
        for i in range(100):
            policy = Policy.create(
                name=f"policy_{i}",
                description=f"Policy {i}",
                effect="allow" if i % 2 == 0 else "deny",
                resource_type="document",
                action="read",
                conditions=[],
                organization_id=sample_context.organization_id,
                created_by=uuid4(),
                priority=i
            )
            policies.append(policy)
        
        mock_repositories['policy_repo'].get_applicable_policies.return_value = policies
        mock_policy_evaluation_service.evaluate_policy.return_value = True

        # Act
        decision = authorization_service.authorize(sample_context)

        # Assert
        # Should handle large number of policies without performance issues
        assert decision.is_denied()  # At least one deny policy exists
        assert len(decision.reasons) > 50  # Should have evaluated many policies

    @patch('time.time')
    def test_authorize_timing_consistency(
        self, 
        mock_time,
        authorization_service, 
        mock_repositories,
        sample_context
    ):
        """Test that authorization timing is consistent and properly tracked."""
        # Arrange
        start_time = 1000.0
        end_time = 1000.5  # 500ms
        mock_time.side_effect = [start_time, end_time]
        
        role = Role.create("user", "User", uuid4(), sample_context.organization_id)
        mock_repositories['role_repo'].get_user_roles.return_value = [role]
        mock_repositories['permission_repo'].get_role_permissions.return_value = []
        mock_repositories['policy_repo'].get_applicable_policies.return_value = []

        # Act
        decision = authorization_service.authorize(sample_context)

        # Assert
        assert decision.evaluation_time_ms == 500.0
        assert mock_time.call_count == 2