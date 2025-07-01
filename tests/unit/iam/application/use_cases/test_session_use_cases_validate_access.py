import pytest
from unittest.mock import Mock
from uuid import uuid4, UUID

from src.iam.application.use_cases.session_use_cases import SessionUseCase
from src.iam.domain.entities.user import User


class TestSessionUseCaseValidateAccess:
    """Test cases for SessionUseCase.validate_session_access method."""

    @pytest.fixture
    def mock_uow(self):
        """Create a mock Unit of Work."""
        uow = Mock()
        uow.get_repository = Mock()
        return uow

    @pytest.fixture
    def mock_repositories(self, mock_uow):
        """Create mock repositories."""
        user_repo = Mock()
        session_repo = Mock()
        role_repo = Mock()
        permission_repo = Mock()
        policy_repo = Mock()
        resource_repo = Mock()

        mock_uow.get_repository.side_effect = lambda name: {
            "user": user_repo,
            "user_session": session_repo,
            "role": role_repo,
            "permission": permission_repo,
            "policy": policy_repo,
            "resource": resource_repo,
            "role_permission": Mock(),
        }[name]

        return {
            "user": user_repo,
            "session": session_repo,
            "role": role_repo,
            "permission": permission_repo,
            "policy": policy_repo,
            "resource": resource_repo,
        }

    @pytest.fixture
    def session_use_case(self, mock_uow, mock_repositories):
        """Create SessionUseCase instance with mocked dependencies."""
        return SessionUseCase(mock_uow)

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return User.create(
            email="test@example.com", name="Test User", password="Password123!"
        )

    @pytest.fixture
    def valid_token(self):
        """Create a valid session token."""
        return "valid-session-token-123"

    @pytest.fixture
    def invalid_token(self):
        """Create an invalid session token."""
        return "invalid-session-token-456"

    def test_validate_session_access_with_invalid_token(
        self, session_use_case, invalid_token
    ):
        """Test validation with invalid session token."""
        # Mock authentication service to return None for invalid token
        session_use_case._auth_service.validate_session = Mock(return_value=None)

        result = session_use_case.validate_session_access(invalid_token)

        assert result is False
        session_use_case._auth_service.validate_session.assert_called_once_with(
            invalid_token
        )

    def test_validate_session_access_with_valid_token_no_permissions(
        self, session_use_case, valid_token, sample_user
    ):
        """Test validation with valid token and no required permissions."""
        # Mock authentication service to return valid user
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        result = session_use_case.validate_session_access(valid_token)

        assert result is True
        session_use_case._auth_service.validate_session.assert_called_once_with(
            valid_token
        )

    def test_validate_session_access_with_valid_token_and_permissions_allowed(
        self, session_use_case, valid_token, sample_user
    ):
        """Test validation with valid token and permissions that are allowed."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock authorization service to allow access
        mock_decision = Mock()
        mock_decision.is_allowed.return_value = True
        session_use_case._authorization_service.authorize = Mock(
            return_value=mock_decision
        )

        required_permissions = ["user:read", "organization:view"]
        result = session_use_case.validate_session_access(
            token=valid_token, required_permissions=required_permissions
        )

        assert result is True
        assert session_use_case._authorization_service.authorize.call_count == 2

    def test_validate_session_access_with_valid_token_and_permissions_denied(
        self, session_use_case, valid_token, sample_user
    ):
        """Test validation with valid token and permissions that are denied."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock authorization service to deny access on second permission
        mock_decision_allow = Mock()
        mock_decision_allow.is_allowed.return_value = True
        mock_decision_deny = Mock()
        mock_decision_deny.is_allowed.return_value = False

        session_use_case._authorization_service.authorize = Mock(
            side_effect=[mock_decision_allow, mock_decision_deny]
        )

        required_permissions = ["user:read", "admin:delete"]
        result = session_use_case.validate_session_access(
            token=valid_token, required_permissions=required_permissions
        )

        assert result is False
        assert session_use_case._authorization_service.authorize.call_count == 2

    def test_validate_session_access_with_organization_scope(
        self, session_use_case, valid_token, sample_user
    ):
        """Test validation with organization scope."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock authorization service
        mock_decision = Mock()
        mock_decision.is_allowed.return_value = True
        session_use_case._authorization_service.authorize = Mock(
            return_value=mock_decision
        )

        org_id = str(uuid4())
        result = session_use_case.validate_session_access(
            token=valid_token,
            required_permissions=["user:read"],
            organization_id=org_id,
        )

        assert result is True

        # Verify the authorization context was created with the organization ID
        call_args = session_use_case._authorization_service.authorize.call_args[0][0]
        assert str(call_args.organization_id) == org_id

    def test_validate_session_access_with_resource_details(
        self, session_use_case, valid_token, sample_user
    ):
        """Test validation with resource type and ID."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock authorization service
        mock_decision = Mock()
        mock_decision.is_allowed.return_value = True
        session_use_case._authorization_service.authorize = Mock(
            return_value=mock_decision
        )

        resource_id = str(uuid4())
        result = session_use_case.validate_session_access(
            token=valid_token,
            required_permissions=["document:edit"],
            resource_type="document",
            resource_id=resource_id,
        )

        assert result is True

        # Verify the authorization context was created with correct resource details
        call_args = session_use_case._authorization_service.authorize.call_args[0][0]
        assert call_args.resource_type == "document"
        assert str(call_args.resource_id) == resource_id

    def test_validate_session_access_with_malformed_permission(
        self, session_use_case, valid_token, sample_user
    ):
        """Test validation with malformed permission string."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock authorization service
        mock_decision = Mock()
        mock_decision.is_allowed.return_value = True
        session_use_case._authorization_service.authorize = Mock(
            return_value=mock_decision
        )

        # Permission without colon should use the whole string as action
        result = session_use_case.validate_session_access(
            token=valid_token,
            required_permissions=["admin_access"],
            resource_type="system",
        )

        assert result is True

        # Verify the authorization context was created correctly
        call_args = session_use_case._authorization_service.authorize.call_args[0][0]
        assert call_args.action == "admin_access"
        assert call_args.resource_type == "system"

    def test_validate_session_access_permission_parsing(
        self, session_use_case, valid_token, sample_user
    ):
        """Test that permissions are correctly parsed."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock authorization service
        mock_decision = Mock()
        mock_decision.is_allowed.return_value = True
        session_use_case._authorization_service.authorize = Mock(
            return_value=mock_decision
        )

        result = session_use_case.validate_session_access(
            token=valid_token, required_permissions=["user:read"]
        )

        assert result is True

        # Verify the authorization context was created with correct parsing
        call_args = session_use_case._authorization_service.authorize.call_args[0][0]
        assert call_args.resource_type == "user"
        assert call_args.action == "read"

    def test_validate_session_access_user_attributes_inclusion(
        self, session_use_case, valid_token, sample_user
    ):
        """Test that user attributes are correctly included in authorization context."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock authorization service
        mock_decision = Mock()
        mock_decision.is_allowed.return_value = True
        session_use_case._authorization_service.authorize = Mock(
            return_value=mock_decision
        )

        result = session_use_case.validate_session_access(
            token=valid_token, required_permissions=["user:read"]
        )

        assert result is True

        # Verify user attributes were included
        call_args = session_use_case._authorization_service.authorize.call_args[0][0]
        user_attributes = call_args.user_attributes

        assert user_attributes["email"] == sample_user.email.value
        assert user_attributes["name"] == sample_user.name
        assert user_attributes["is_active"] == sample_user.is_active
        assert user_attributes["is_verified"] == sample_user.is_verified

    def test_validate_session_access_simple_method(
        self, session_use_case, valid_token, sample_user
    ):
        """Test the simplified validate_session_access_simple method."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock authorization service
        mock_decision = Mock()
        mock_decision.is_allowed.return_value = True
        session_use_case._authorization_service.authorize = Mock(
            return_value=mock_decision
        )

        result = session_use_case.validate_session_access_simple(
            token=valid_token, action="read", resource_type="user"
        )

        assert result is True

        # Verify it calls the main method with correct permission format
        call_args = session_use_case._authorization_service.authorize.call_args[0][0]
        assert call_args.resource_type == "user"
        assert call_args.action == "read"

    def test_validate_session_access_simple_with_default_resource(
        self, session_use_case, valid_token, sample_user
    ):
        """Test simplified method with default resource type."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock authorization service
        mock_decision = Mock()
        mock_decision.is_allowed.return_value = True
        session_use_case._authorization_service.authorize = Mock(
            return_value=mock_decision
        )

        result = session_use_case.validate_session_access_simple(
            token=valid_token, action="manage"
        )

        assert result is True

        # Verify default resource type "system" was used
        call_args = session_use_case._authorization_service.authorize.call_args[0][0]
        assert call_args.resource_type == "system"
        assert call_args.action == "manage"

    def test_get_session_user_permissions_invalid_token(
        self, session_use_case, invalid_token
    ):
        """Test getting user permissions with invalid token."""
        # Mock authentication service to return None
        session_use_case._auth_service.validate_session = Mock(return_value=None)

        result = session_use_case.get_session_user_permissions(invalid_token)

        assert result == []

    def test_get_session_user_permissions_valid_token(
        self, session_use_case, valid_token, sample_user
    ):
        """Test getting user permissions with valid token."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock RBAC service method
        expected_permissions = ["user:read", "user:write", "organization:view"]
        session_use_case._authorization_service._rbac_service.get_user_permissions = (
            Mock(return_value=expected_permissions)
        )

        result = session_use_case.get_session_user_permissions(valid_token)

        assert result == expected_permissions
        session_use_case._authorization_service._rbac_service.get_user_permissions.assert_called_once_with(
            user_id=sample_user.id, organization_id=None
        )

    def test_get_session_user_permissions_with_organization(
        self, session_use_case, valid_token, sample_user
    ):
        """Test getting user permissions with organization scope."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock RBAC service method
        expected_permissions = ["org:admin", "user:manage"]
        session_use_case._authorization_service._rbac_service.get_user_permissions = (
            Mock(return_value=expected_permissions)
        )

        org_id = str(uuid4())
        result = session_use_case.get_session_user_permissions(valid_token, org_id)

        assert result == expected_permissions

        # Verify organization UUID conversion
        call_args = session_use_case._authorization_service._rbac_service.get_user_permissions.call_args
        assert str(call_args[1]["organization_id"]) == org_id

    def test_uuid_conversion_in_authorization_context(
        self, session_use_case, valid_token, sample_user
    ):
        """Test that string UUIDs are properly converted in authorization context."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock authorization service
        mock_decision = Mock()
        mock_decision.is_allowed.return_value = True
        session_use_case._authorization_service.authorize = Mock(
            return_value=mock_decision
        )

        org_id_str = str(uuid4())
        resource_id_str = str(uuid4())

        result = session_use_case.validate_session_access(
            token=valid_token,
            required_permissions=["document:read"],
            organization_id=org_id_str,
            resource_id=resource_id_str,
        )

        assert result is True

        # Verify UUIDs were properly converted
        call_args = session_use_case._authorization_service.authorize.call_args[0][0]
        assert isinstance(call_args.organization_id, UUID)
        assert isinstance(call_args.resource_id, UUID)
        assert str(call_args.organization_id) == org_id_str
        assert str(call_args.resource_id) == resource_id_str

    def test_multiple_permissions_all_allowed(
        self, session_use_case, valid_token, sample_user
    ):
        """Test validation with multiple permissions that are all allowed."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock authorization service to allow all permissions
        mock_decision = Mock()
        mock_decision.is_allowed.return_value = True
        session_use_case._authorization_service.authorize = Mock(
            return_value=mock_decision
        )

        required_permissions = [
            "user:read",
            "user:write",
            "organization:view",
            "admin:manage",
        ]
        result = session_use_case.validate_session_access(
            token=valid_token, required_permissions=required_permissions
        )

        assert result is True
        assert session_use_case._authorization_service.authorize.call_count == 4

    def test_authorization_context_user_id_consistency(
        self, session_use_case, valid_token, sample_user
    ):
        """Test that the user ID in authorization context matches the session user."""
        # Mock authentication service
        session_use_case._auth_service.validate_session = Mock(return_value=sample_user)

        # Mock authorization service
        mock_decision = Mock()
        mock_decision.is_allowed.return_value = True
        session_use_case._authorization_service.authorize = Mock(
            return_value=mock_decision
        )

        result = session_use_case.validate_session_access(
            token=valid_token, required_permissions=["user:read"]
        )

        assert result is True

        # Verify user ID consistency
        call_args = session_use_case._authorization_service.authorize.call_args[0][0]
        assert call_args.user_id == sample_user.id
