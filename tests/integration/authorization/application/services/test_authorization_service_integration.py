import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock, MagicMock

from src.authorization.domain.entities.authorization_context import AuthorizationContext
from src.authorization.domain.entities.role import Role
from src.authorization.domain.entities.permission import Permission, PermissionAction
from src.authorization.domain.entities.policy import (
    Policy,
    PolicyCondition,
    PolicyEffect,
)
from src.authorization.domain.entities.resource import Resource
from src.authorization.domain.services.authorization_service import AuthorizationService
from src.authorization.domain.services.rbac_service import RBACService
from src.authorization.domain.services.abac_service import ABACService
from src.authorization.domain.services.policy_evaluation_service import (
    PolicyEvaluationService,
)
from src.authorization.domain.value_objects.authorization_decision import (
    AuthorizationDecision,
    DecisionReason,
    DecisionResult,
)
from src.authorization.domain.value_objects.role_name import RoleName
from src.authorization.domain.value_objects.permission_name import PermissionName


class TestAuthorizationServiceIntegration:
    """Integration tests for AuthorizationService authorize function."""

    @pytest.fixture
    def mock_role_repository(self):
        """Create a mock role repository."""
        return Mock()

    @pytest.fixture
    def mock_permission_repository(self):
        """Create a mock permission repository."""
        return Mock()

    @pytest.fixture
    def mock_role_permission_repository(self):
        """Create a mock role permission repository."""
        return Mock()

    @pytest.fixture
    def mock_policy_repository(self):
        """Create a mock policy repository."""
        return Mock()

    @pytest.fixture
    def mock_resource_repository(self):
        """Create a mock resource repository."""
        return Mock()

    @pytest.fixture
    def mock_policy_evaluation_service(self):
        """Create a mock policy evaluation service."""
        return Mock(spec=PolicyEvaluationService)

    @pytest.fixture
    def rbac_service(
        self,
        mock_role_repository,
        mock_permission_repository,
        mock_role_permission_repository,
    ):
        """Create RBAC service instance."""
        return RBACService(
            mock_role_repository,
            mock_permission_repository,
            mock_role_permission_repository,
        )

    @pytest.fixture
    def abac_service(
        self,
        mock_policy_repository,
        mock_resource_repository,
        mock_policy_evaluation_service,
    ):
        """Create ABAC service instance."""
        return ABACService(
            mock_policy_repository,
            mock_resource_repository,
            mock_policy_evaluation_service,
        )

    @pytest.fixture
    def authorization_service(self, rbac_service, abac_service):
        """Create AuthorizationService instance."""
        return AuthorizationService(rbac_service, abac_service)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID."""
        return uuid4()

    @pytest.fixture
    def sample_organization_id(self):
        """Sample organization ID."""
        return uuid4()

    @pytest.fixture
    def sample_resource_id(self):
        """Sample resource ID."""
        return uuid4()

    @pytest.fixture
    def sample_role(self, sample_organization_id):
        """Create a sample role."""
        return Role.create(
            name="admin",
            description="Administrator role",
            created_by=uuid4(),
            organization_id=sample_organization_id,
        )

    @pytest.fixture
    def sample_permission(self):
        """Create a sample permission."""
        return Permission.create(
            name="read_users",
            description="Read users permission",
            action=PermissionAction.READ,
            resource_type="user",
        )

    @pytest.fixture
    def sample_policy(self, sample_organization_id):
        """Create a sample policy."""
        return Policy.create(
            name="owner_policy",
            description="Resource owner policy",
            effect=PolicyEffect.ALLOW,
            resource_type="document",
            action="read",
            conditions=[
                PolicyCondition(
                    attribute="user.id",
                    operator="eq",
                    value="resource.owner_id",
                )
            ],
            organization_id=sample_organization_id,
            created_by=uuid4(),
        )

    @pytest.fixture
    def sample_resource(self, sample_organization_id, sample_user_id):
        """Create a sample resource."""
        return Resource.create(
            # name="Test Document",
            resource_type="document",
            organization_id=sample_organization_id,
            owner_id=sample_user_id,
            resource_id=uuid4(),
            # metadata={"department": "engineering"},
            attributes={"department": "engineering"},
        )

    def test_authorize_rbac_allow_no_abac_policies(
        self,
        authorization_service,
        mock_role_repository,
        mock_permission_repository,
        mock_policy_repository,
        sample_user_id,
        sample_organization_id,
        sample_role,
        sample_permission,
    ):
        """Test authorization when RBAC allows and no ABAC policies exist."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=sample_user_id,
            resource_type="user",
            action="read",
            organization_id=sample_organization_id,
        )

        # Mock RBAC to allow
        mock_role_repository.get_user_roles.return_value = [sample_role]
        mock_role_repository.get_role_hierarchy.return_value = [sample_role]
        mock_permission_repository.get_role_permissions.return_value = [
            sample_permission
        ]

        # Mock ABAC to have no policies
        mock_policy_repository.get_applicable_policies.return_value = []

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_allowed()
        assert decision.result == DecisionResult.ALLOW
        assert any(reason.type == "rbac_allow" for reason in decision.reasons)
        assert any(reason.type == "abac_no_policies" for reason in decision.reasons)
        assert decision.evaluation_time_ms > 0

    def test_authorize_rbac_allow_abac_deny(
        self,
        authorization_service,
        mock_role_repository,
        mock_permission_repository,
        mock_policy_repository,
        mock_policy_evaluation_service,
        sample_user_id,
        sample_organization_id,
        sample_role,
        sample_permission,
        sample_policy,
    ):
        """Test authorization when RBAC allows but ABAC denies."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=sample_user_id,
            resource_type="document",
            action="read",
            organization_id=sample_organization_id,
        )

        # Mock RBAC to allow
        mock_role_repository.get_user_roles.return_value = [sample_role]
        mock_role_repository.get_role_hierarchy.return_value = mock_role_repository.get_user_roles.return_value
        mock_permission_repository.get_role_permissions.return_value = [
            Permission.create(
                name="read_documents",
                description="Read documents permission",
                action=PermissionAction.READ,
                resource_type="document",
            )
        ]

        # Mock ABAC to deny
        deny_policy = Policy.create(
            name="deny_policy",
            description="Deny policy",
            effect=PolicyEffect.DENY,
            resource_type="document",
            action="read",
            conditions=[
                PolicyCondition(
                    attribute="user.department", operator="eq", value="finance"
                )
            ],
            organization_id=sample_organization_id,
            created_by=uuid4(),
        )
        mock_policy_repository.get_applicable_policies.return_value = [deny_policy]
        mock_policy_evaluation_service.evaluate_policy.return_value = (
            True  # Policy applies and denies
        )

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_denied()
        assert decision.result == DecisionResult.DENY
        assert any(reason.type == "rbac_allow" for reason in decision.reasons)
        assert any(reason.type == "policy_evaluation" for reason in decision.reasons)

    def test_authorize_rbac_deny_abac_allow(
        self,
        authorization_service,
        mock_role_repository,
        mock_permission_repository,
        mock_policy_repository,
        mock_policy_evaluation_service,
        sample_user_id,
        sample_organization_id,
        sample_role,
        sample_policy,
    ):
        """Test authorization when RBAC denies but ABAC allows."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=sample_user_id,
            resource_type="document",
            action="read",
            organization_id=sample_organization_id,
        )

        # Mock RBAC to deny (no permissions)
        mock_role_repository.get_user_roles.return_value = [sample_role]
        mock_role_repository.get_role_hierarchy.return_value = mock_role_repository.get_user_roles.return_value
        mock_permission_repository.get_role_permissions.return_value = []  # No permissions

        # Mock ABAC to allow
        allow_policy = Policy.create(
            name="allow_policy",
            description="Allow policy",
            effect=PolicyEffect.ALLOW,
            resource_type="document",
            action="read",
            conditions=[
                PolicyCondition(
                    attribute="user.id",
                    operator="eq",
                    value="resource.owner_id",
                )
            ],
            organization_id=sample_organization_id,
            created_by=uuid4(),
        )
        mock_policy_repository.get_applicable_policies.return_value = [allow_policy]
        mock_policy_evaluation_service.evaluate_policy.return_value = (
            True  # Policy applies and allows
        )

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_allowed()
        assert decision.result == DecisionResult.ALLOW
        assert any(reason.type == "rbac_no_permissions" for reason in decision.reasons)
        assert any(reason.type == "policy_evaluation" for reason in decision.reasons)

    def test_authorize_both_deny(
        self,
        authorization_service,
        mock_role_repository,
        mock_permission_repository,
        mock_policy_repository,
        mock_policy_evaluation_service,
        sample_user_id,
        sample_organization_id,
        sample_role,
    ):
        """Test authorization when both RBAC and ABAC deny."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=sample_user_id,
            resource_type="document",
            action="delete",
            organization_id=sample_organization_id,
        )

        # Mock RBAC to deny
        mock_role_repository.get_user_roles.return_value = [sample_role]
        mock_role_repository.get_role_hierarchy.return_value = mock_role_repository.get_user_roles.return_value
        mock_permission_repository.get_role_permissions.return_value = []  # No permissions

        # Mock ABAC to deny
        deny_policy = Policy.create(
            name="deny_policy",
            description="Deny policy",
            effect=PolicyEffect.DENY,
            resource_type="document",
            action="delete",
            conditions=[
                PolicyCondition(
                    attribute="always",
                    operator="eq",
                    value="True",
                )
            ],
            organization_id=sample_organization_id,
            created_by=uuid4(),
        )
        mock_policy_repository.get_applicable_policies.return_value = [deny_policy]
        mock_policy_evaluation_service.evaluate_policy.return_value = True

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_denied()
        assert decision.result == DecisionResult.DENY
        assert any(reason.type == "rbac_no_permissions" for reason in decision.reasons)
        assert any(reason.type == "policy_evaluation" for reason in decision.reasons)

    def test_authorize_no_roles_no_policies(
        self,
        authorization_service,
        mock_role_repository,
        mock_policy_repository,
        sample_user_id,
        sample_organization_id,
    ):
        """Test authorization when user has no roles and no policies exist."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=sample_user_id,
            resource_type="document",
            action="read",
            organization_id=sample_organization_id,
        )

        # Mock no roles
        mock_role_repository.get_user_roles.return_value = []
        mock_role_repository.get_role_hierarchy.return_value = mock_role_repository.get_user_roles.return_value

        # Mock no policies
        mock_policy_repository.get_applicable_policies.return_value = []

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_denied()
        assert decision.result == DecisionResult.DENY
        assert any(reason.type == "rbac_no_roles" for reason in decision.reasons)
        assert any(reason.type == "abac_no_policies" for reason in decision.reasons)

    def test_authorize_default_deny(
        self,
        authorization_service,
        mock_role_repository,
        mock_permission_repository,
        mock_policy_repository,
        mock_policy_evaluation_service,
        sample_user_id,
        sample_organization_id,
        sample_role,
    ):
        """Test default deny when no applicable rules found."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=sample_user_id,
            resource_type="unknown",
            action="unknown",
            organization_id=sample_organization_id,
        )

        # Mock RBAC to have role but no matching permissions
        mock_role_repository.get_user_roles.return_value = [sample_role]
        mock_role_repository.get_role_hierarchy.return_value = mock_role_repository.get_user_roles.return_value
        mock_permission_repository.get_role_permissions.return_value = [
            Permission.create(
                name="read_users",
                description="Read users",
                action=PermissionAction.READ,
                resource_type="user",
            )
        ]

        # Mock ABAC to have policies but none applicable
        mock_policy_repository.get_applicable_policies.return_value = []

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_denied()
        assert decision.result == DecisionResult.DENY
        assert any(reason.type == "rbac_deny" for reason in decision.reasons)

    def test_authorize_with_wildcard_permissions(
        self,
        authorization_service,
        mock_role_repository,
        mock_permission_repository,
        mock_policy_repository,
        mock_resource_repository,
        sample_user_id,
        sample_organization_id,
        sample_role,
    ):
        """Test authorization with wildcard permissions."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=sample_user_id,
            resource_type="document",
            action=PermissionAction.MANAGE,
            organization_id=sample_organization_id,
        )

        # Mock RBAC with wildcard permission
        wildcard_permission = Permission(
            id=uuid4(),
            name=PermissionName(value="wildcard_all"),
            description="Global wildcard permission",
            action=PermissionAction.MANAGE,
            resource_type="*",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            is_system_permission=False,
        )
        mock_role_repository.get_user_roles.return_value = [sample_role]
        mock_role_repository.get_role_hierarchy.return_value = mock_role_repository.get_user_roles.return_value
        mock_permission_repository.get_role_permissions.return_value = [
            wildcard_permission
        ]

        # Mock no ABAC policies
        mock_policy_repository.get_applicable_policies.return_value = []
        mock_resource_repository.get_by_resource_id.return_value = None

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_allowed()
        assert decision.result == DecisionResult.ALLOW
        assert any(reason.type == "rbac_allow" for reason in decision.reasons)
        assert any(
            "action wildcard" in reason.message
            for reason in decision.reasons
            if reason.type == "rbac_allow"
        )

    def test_authorize_multiple_policies_deny_overrides(
        self,
        authorization_service,
        mock_role_repository,
        mock_permission_repository,
        mock_policy_repository,
        mock_policy_evaluation_service,
        sample_user_id,
        sample_organization_id,
        sample_role,
    ):
        """Test authorization with multiple policies where deny overrides allow."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=sample_user_id,
            resource_type="document",
            action="read",
            organization_id=sample_organization_id,
        )

        # Mock RBAC to allow
        doc_permission = Permission.create(
            name="read_documents",
            description="Read documents",
            action=PermissionAction.READ,
            resource_type="document",
        )
        mock_role_repository.get_user_roles.return_value = [sample_role]
        mock_role_repository.get_role_hierarchy.return_value = mock_role_repository.get_user_roles.return_value
        mock_permission_repository.get_role_permissions.return_value = [doc_permission]

        # Mock ABAC with both allow and deny policies
        allow_policy = Policy.create(
            name="allow_policy",
            description="Allow policy",
            effect=PolicyEffect.ALLOW,
            resource_type="document",
            action="read",
            conditions=[],
            organization_id=sample_organization_id,
            created_by=uuid4(),
            priority=10,
        )
        deny_policy = Policy.create(
            name="deny_policy",
            description="Deny policy",
            effect=PolicyEffect.DENY,
            resource_type="document",
            action="read",
            conditions=[],
            organization_id=sample_organization_id,
            created_by=uuid4(),
            priority=20,
        )

        mock_policy_repository.get_applicable_policies.return_value = [
            allow_policy,
            deny_policy,
        ]
        # Both policies apply
        mock_policy_evaluation_service.evaluate_policy.return_value = True

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_denied()  # Deny overrides allow
        assert decision.result == DecisionResult.DENY
        assert any(reason.type == "rbac_allow" for reason in decision.reasons)
        assert len([r for r in decision.reasons if r.type == "policy_evaluation"]) == 2

    def test_authorize_with_resource_enrichment(
        self,
        authorization_service,
        mock_role_repository,
        mock_permission_repository,
        mock_policy_repository,
        mock_resource_repository,
        mock_policy_evaluation_service,
        sample_user_id,
        sample_organization_id,
        sample_resource_id,
        sample_role,
        sample_resource,
    ):
        """Test authorization with resource attribute enrichment."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=sample_user_id,
            resource_type="document",
            action="read",
            organization_id=sample_organization_id,
            resource_id=sample_resource_id,
        )

        # Mock RBAC to deny
        mock_role_repository.get_user_roles.return_value = [sample_role]
        mock_role_repository.get_role_hierarchy.return_value = mock_role_repository.get_user_roles.return_value
        mock_permission_repository.get_role_permissions.return_value = []

        # Mock resource repository to return sample resource
        mock_resource_repository.get_by_resource_id.return_value = sample_resource

        # Mock ABAC with ownership policy
        ownership_policy = Policy.create(
            name="ownership_policy",
            description="Owner can read",
            effect=PolicyEffect.ALLOW,
            resource_type="document",
            action="read",
            conditions=[
                PolicyCondition(
                    attribute="user_id", operator="eq", value="{{resource.owner_id}}"
                )
            ],
            organization_id=sample_organization_id,
            created_by=uuid4(),
        )
        mock_policy_repository.get_applicable_policies.return_value = [ownership_policy]
        mock_policy_evaluation_service.evaluate_policy.return_value = True

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_allowed()
        assert decision.result == DecisionResult.ALLOW
        assert any(reason.type == "policy_evaluation" for reason in decision.reasons)
        # Verify resource repository was called for enrichment
        mock_resource_repository.get_by_resource_id.assert_called_once_with(
            "document", sample_resource_id
        )

    def test_authorize_error_handling(
        self,
        authorization_service,
        mock_role_repository,
        sample_user_id,
        sample_organization_id,
    ):
        """Test authorization error handling."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=sample_user_id,
            resource_type="document",
            action="read",
            organization_id=sample_organization_id,
        )

        # Mock exception in RBAC
        mock_role_repository.get_user_roles.side_effect = Exception("Database error")

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_denied()
        assert decision.result == DecisionResult.DENY
        assert any(reason.type == "authorization_error" for reason in decision.reasons)
        assert any("Database error" in reason.message for reason in decision.reasons)
        assert decision.evaluation_time_ms > 0

    def test_authorize_performance_metrics(
        self,
        authorization_service,
        mock_role_repository,
        mock_policy_repository,
        sample_user_id,
        sample_organization_id,
        sample_role,
    ):
        """Test that authorization tracks performance metrics."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=sample_user_id,
            resource_type="document",
            action="read",
            organization_id=sample_organization_id,
        )

        mock_role_repository.get_user_roles.return_value = [sample_role]
        mock_role_repository.get_role_hierarchy.return_value = mock_role_repository.get_user_roles.return_value
        mock_policy_repository.get_applicable_policies.return_value = []

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.evaluation_time_ms > 0
        assert decision.evaluated_at is not None
        assert isinstance(decision.evaluated_at, datetime)

    def test_can_user_access_resource(
        self,
        authorization_service,
        mock_role_repository,
        mock_permission_repository,
        mock_policy_repository,
        mock_resource_repository,
        sample_user_id,
        sample_organization_id,
        # sample_resource_id,
        sample_role,
        sample_permission,
        sample_resource,
    ):
        """Test simplified can_user_access_resource method."""
        # Arrange
        mock_role_repository.get_user_roles.return_value = [sample_role]
        mock_role_repository.get_role_hierarchy.return_value = mock_role_repository.get_user_roles.return_value
        mock_permission_repository.get_role_permissions.return_value = [
            sample_permission
        ]
        mock_policy_repository.get_applicable_policies.return_value = []
        mock_resource_repository.get_by_resource_id.return_value = None

        # Act
        result = authorization_service.can_user_access_resource(
            user_id=sample_user_id,
            resource_type="user",
            resource_id=sample_resource.id,
            action="read",
            organization_id=sample_organization_id,
        )

        # Assert
        assert result is True

    def test_check_multiple_permissions(
        self,
        authorization_service,
        mock_role_repository,
        mock_permission_repository,
        mock_policy_repository,
        mock_resource_repository,
        sample_user_id,
        sample_organization_id,
        sample_role,
    ):
        """Test checking multiple permissions at once."""
        # Arrange
        permissions = [
            Permission.create(
                name="read_users",
                description="Read users",
                action=PermissionAction.READ,
                resource_type="user",
            ),
            Permission.create(
                name="write_users",
                description="Write users",
                action=PermissionAction.UPDATE,
                resource_type="user",
            ),
        ]
        mock_role_repository.get_user_roles.return_value = [sample_role]
        mock_role_repository.get_role_hierarchy.return_value = mock_role_repository.get_user_roles.return_value
        mock_permission_repository.get_role_permissions.return_value = permissions
        mock_policy_repository.get_applicable_policies.return_value = []
        mock_resource_repository.get_by_resource_id.return_value = None

        actions = ["read", "update", "delete"]

        # Act
        results = authorization_service.check_multiple_permissions(
            user_id=sample_user_id,
            resource_type="user",
            actions=actions,
            organization_id=sample_organization_id,
        )

        # Assert
        assert results["read"] is True
        assert results["update"] is True
        assert results["delete"] is False  # No delete permission
        assert len(results) == 3

    def test_authorize_with_user_attributes(
        self,
        authorization_service,
        mock_role_repository,
        mock_permission_repository,
        mock_policy_repository,
        mock_policy_evaluation_service,
        sample_user_id,
        sample_organization_id,
        sample_role,
    ):
        """Test authorization with user attributes in context."""
        # Arrange
        context = AuthorizationContext.create(
            user_id=sample_user_id,
            resource_type="document",
            action="read",
            organization_id=sample_organization_id,
            user_attributes={"department": "engineering", "clearance_level": 3},
        )

        # Mock RBAC to deny
        mock_role_repository.get_user_roles.return_value = [sample_role]
        mock_role_repository.get_role_hierarchy.return_value = mock_role_repository.get_user_roles.return_value
        mock_permission_repository.get_role_permissions.return_value = []

        # Mock ABAC with department-based policy
        dept_policy = Policy.create(
            name="dept_policy",
            description="Department access",
            effect=PolicyEffect.ALLOW,
            resource_type="document",
            action="read",
            conditions=[
                PolicyCondition(
                    attribute="user.department", operator="eq", value="engineering"
                )
            ],
            organization_id=sample_organization_id,
            created_by=uuid4(),
        )
        mock_policy_repository.get_applicable_policies.return_value = [dept_policy]
        mock_policy_evaluation_service.evaluate_policy.return_value = True

        # Act
        decision = authorization_service.authorize(context)

        # Assert
        assert decision.is_allowed()
        assert decision.result == DecisionResult.ALLOW
        # Verify context was passed to policy evaluation with user attributes
        mock_policy_evaluation_service.evaluate_policy.assert_called_once()
        call_args = mock_policy_evaluation_service.evaluate_policy.call_args[0]
        passed_context = call_args[1]
        assert passed_context.user_attributes["department"] == "engineering"
        assert passed_context.user_attributes["clearance_level"] == 3
