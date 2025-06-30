import pytest
from unittest.mock import Mock, Mock
from uuid import uuid4
from user.application.use_cases.auth_use_cases import AuthUseCases
from user.application.dtos.auth_dto import SignupDto, LoginDto
from user.application.services.jwt_service import JWTService
from user.domain.entities.user import User
from tests.factories.user_factory import UserFactory


class TestAuthUseCases:
    """Unit tests for AuthUseCases."""

    @pytest.fixture
    def mock_uow(self):
        """Mock Unit of Work."""
        uow = Mock()
        uow.users = Mock()
        uow.user_sessions = Mock()
        uow.__aenter__ = Mock(return_value=uow)
        uow.__aexit__ = Mock()
        return uow

    @pytest.fixture
    def mock_jwt_service(self):
        """Mock JWT Service."""
        service = Mock(spec=JWTService)
        service.access_token_expire_minutes = 60
        service.create_access_token.return_value = ("test_token", None)
        service.verify_token.return_value = Mock(
            user_id=uuid4(), email="test@example.com"
        )
        service.is_token_expired.return_value = False
        return service

    @pytest.fixture
    def auth_use_cases(self, mock_uow, mock_jwt_service):
        """Create AuthUseCases instance with mocked dependencies."""
        return AuthUseCases(mock_uow, mock_jwt_service)

    @pytest.mark.io
    def test_signup_success(self, auth_use_cases, mock_uow):
        """Test successful user signup."""
        # Arrange
        signup_data = SignupDto(
            email="test@example.com", name="Test User", password="password123"
        )

        mock_uow.users.get_by_email.return_value = None  # No existing user
        created_user = UserFactory.create_user(
            email="test@example.com", name="Test User", password="password123"
        )
        mock_uow.users.create.return_value = created_user

        # Mock session creation
        auth_use_cases.session_use_cases.create_session = Mock(
            return_value=(Mock(), "test_token")
        )

        # Act
        result = auth_use_cases.signup(
            signup_data, ip_address="192.168.1.1", user_agent="Test Agent"
        )

        # Assert
        assert result.access_token == "test_token"
        assert result.token_type == "bearer"
        assert result.expires_in == 3600  # 60 minutes
        assert result.user.email == "test@example.com"
        assert result.user.name == "Test User"

        mock_uow.users.get_by_email.assert_called_once_with("test@example.com")
        mock_uow.users.create.assert_called_once()
        auth_use_cases.session_use_cases.create_session.assert_called_once()

    @pytest.mark.io
    def test_signup_user_already_exists(self, auth_use_cases, mock_uow):
        """Test signup with existing user email."""
        # Arrange
        signup_data = SignupDto(
            email="existing@example.com", name="Test User", password="password123"
        )

        existing_user = UserFactory.create_user(email="existing@example.com")
        mock_uow.users.get_by_email.return_value = existing_user

        # Act & Assert
        with pytest.raises(
            ValueError, match="User with email existing@example.com already exists"
        ):
            auth_use_cases.signup(signup_data)

    @pytest.mark.io
    def test_login_success(self, auth_use_cases, mock_uow):
        """Test successful user login."""
        # Arrange
        login_data = LoginDto(email="test@example.com", password="password123")

        user = UserFactory.create_user(email="test@example.com", password="password123")
        mock_uow.users.get_by_email.return_value = user

        # Mock session creation
        auth_use_cases.session_use_cases.create_session = Mock(
            return_value=(Mock(), "test_token")
        )

        # Act
        result = auth_use_cases.login(
            login_data, ip_address="192.168.1.1", user_agent="Test Agent"
        )

        # Assert
        assert result is not None
        assert result.access_token == "test_token"
        assert result.user.email == "test@example.com"

        mock_uow.users.get_by_email.assert_called_once_with("test@example.com")
        auth_use_cases.session_use_cases.create_session.assert_called_once()

    @pytest.mark.io
    def test_login_user_not_found(self, auth_use_cases, mock_uow):
        """Test login with non-existent user."""
        # Arrange
        login_data = LoginDto(email="nonexistent@example.com", password="password123")

        mock_uow.users.get_by_email.return_value = None

        # Act
        result = auth_use_cases.login(login_data)

        # Assert
        assert result is None

    @pytest.mark.io
    def test_login_inactive_user(self, auth_use_cases, mock_uow):
        """Test login with inactive user."""
        # Arrange
        login_data = LoginDto(email="inactive@example.com", password="password123")

        inactive_user = UserFactory.create_inactive_user(
            email="inactive@example.com", password="password123"
        )
        mock_uow.users.get_by_email.return_value = inactive_user

        # Act & Assert
        with pytest.raises(ValueError, match="User account is deactivated"):
            auth_use_cases.login(login_data)

    @pytest.mark.io
    def test_login_wrong_password(self, auth_use_cases, mock_uow):
        """Test login with wrong password."""
        # Arrange
        login_data = LoginDto(email="test@example.com", password="wrongpassword")

        user = UserFactory.create_user(email="test@example.com", password="password123")
        mock_uow.users.get_by_email.return_value = user

        # Act
        result = auth_use_cases.login(login_data)

        # Assert
        assert result is None

    @pytest.mark.io
    def test_get_current_user_success(self, auth_use_cases, mock_uow, mock_jwt_service):
        """Test getting current user with valid token."""
        # Arrange
        token = "valid_token"
        user = UserFactory.create_user()

        # Mock session validation
        auth_use_cases.session_use_cases.validate_session = Mock(
            return_value=Mock()  # Valid session
        )

        mock_jwt_service.verify_token.return_value = Mock(
            user_id=user.id, email=str(user.email.value)
        )
        mock_uow.users.get_by_id.return_value = user

        # Act
        result = auth_use_cases.get_current_user(token)

        # Assert
        assert result is not None
        assert result.id == user.id
        assert result.email == str(user.email.value)

        auth_use_cases.session_use_cases.validate_session.assert_called_once_with(token)
        mock_jwt_service.verify_token.assert_called_once_with(token)
        mock_uow.users.get_by_id.assert_called_once_with(user.id)

    @pytest.mark.io
    def test_get_current_user_invalid_session(self, auth_use_cases):
        """Test getting current user with invalid session."""
        # Arrange
        token = "invalid_token"

        # Mock session validation failure
        auth_use_cases.session_use_cases.validate_session = Mock(
            return_value=None  # Invalid session
        )

        # Act
        result = auth_use_cases.get_current_user(token)

        # Assert
        assert result is None

    @pytest.mark.io
    def test_get_current_user_invalid_token(self, auth_use_cases, mock_jwt_service):
        """Test getting current user with invalid token."""
        # Arrange
        token = "invalid_token"

        # Mock session validation success but token verification failure
        auth_use_cases.session_use_cases.validate_session = Mock(
            return_value=Mock()  # Valid session
        )
        mock_jwt_service.verify_token.return_value = None

        # Act
        result = auth_use_cases.get_current_user(token)

        # Assert
        assert result is None

    @pytest.mark.io
    def test_get_current_user_inactive_user(
        self, auth_use_cases, mock_uow, mock_jwt_service
    ):
        """Test getting current user with inactive user."""
        # Arrange
        token = "valid_token"
        inactive_user = UserFactory.create_inactive_user()

        # Mock session validation
        auth_use_cases.session_use_cases.validate_session = Mock(
            return_value=Mock()  # Valid session
        )

        mock_jwt_service.verify_token.return_value = Mock(
            user_id=inactive_user.id, email=str(inactive_user.email.value)
        )
        mock_uow.users.get_by_id.return_value = inactive_user

        # Act
        result = auth_use_cases.get_current_user(token)

        # Assert
        assert result is None

    @pytest.mark.io
    def test_verify_token_valid(self, auth_use_cases):
        """Test token verification with valid token."""
        # Arrange
        token = "valid_token"

        # Mock session validation
        auth_use_cases.session_use_cases.validate_session = Mock(
            return_value=Mock()  # Valid session
        )

        # Act
        result = auth_use_cases.verify_token(token)

        # Assert
        assert result is True

    @pytest.mark.io
    def test_verify_token_invalid(self, auth_use_cases):
        """Test token verification with invalid token."""
        # Arrange
        token = "invalid_token"

        # Mock session validation failure
        auth_use_cases.session_use_cases.validate_session = Mock(
            return_value=None  # Invalid session
        )

        # Act
        result = auth_use_cases.verify_token(token)

        # Assert
        assert result is False

    @pytest.mark.io
    def test_logout_success(self, auth_use_cases):
        """Test successful logout."""
        # Arrange
        token = "valid_token"

        # Mock session logout
        auth_use_cases.session_use_cases.logout_session = Mock()

        # Act
        result = auth_use_cases.logout(token)

        # Assert
        assert result is True
        auth_use_cases.session_use_cases.logout_session.assert_called_once_with(token)

    @pytest.mark.io
    def test_logout_failure(self, auth_use_cases):
        """Test logout failure."""
        # Arrange
        token = "invalid_token"

        # Mock session logout failure
        auth_use_cases.session_use_cases.logout_session = Mock(
            side_effect=ValueError("Session not found")
        )

        # Act
        result = auth_use_cases.logout(token)

        # Assert
        assert result is False
