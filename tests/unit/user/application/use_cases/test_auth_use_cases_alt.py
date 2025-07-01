import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from user.application.use_cases.auth_use_cases import AuthUseCase
from user.application.dtos.auth_dto import (
    LoginDTO,
    LogoutDTO,
    AuthResponseDTO,
    PasswordResetRequestDTO,
    PasswordResetConfirmDTO
)
from user.domain.entities.user import User
from user.domain.entities.user_session import UserSession, SessionStatus


class TestAuthUseCase:
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_uow = Mock()
        self.mock_user_repository = Mock()
        self.mock_session_repository = Mock()
        self.mock_auth_service = Mock()
        
        def get_repository(name):
            if name == "user":
                return self.mock_user_repository
            elif name == "user_session":
                return self.mock_session_repository
            return None
        
        self.mock_uow.get_repository.side_effect = get_repository
        self.mock_uow.__enter__ = Mock(return_value=self.mock_uow)
        self.mock_uow.__exit__ = Mock(return_value=None)
        
        # Create use case and manually set the auth service
        self.use_case = AuthUseCase(self.mock_uow)
        self.use_case._auth_service = self.mock_auth_service

    def test_login_successful(self):
        """Test successful user login."""
        dto = LoginDTO(
            email="test@example.com",
            password="SecurePass123",
            remember_me=False,
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1"
        )
        
        user = User.create(
            email=dto.email,
            name="Test User",
            password=dto.password
        )
        
        session = UserSession.create(
            user_id=user.id,
            session_token="test_token_123",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        # Mock authentication service
        self.mock_auth_service.authenticate.return_value = user
        self.mock_auth_service.create_session.return_value = session
        
        with patch.object(self.use_case, '_generate_session_token', return_value="test_token_123"):
            result = self.use_case.login(dto)
        
        assert isinstance(result, AuthResponseDTO)
        assert result.user.email == dto.email
        assert result.access_token == "test_token_123"
        assert result.expires_in == 24 * 3600  # 24 hours in seconds
        
        # Verify service calls
        self.mock_auth_service.authenticate.assert_called_once_with(dto.email, dto.password)
        self.mock_auth_service.create_session.assert_called_once()

    def test_login_remember_me(self):
        """Test login with remember me option."""
        dto = LoginDTO(
            email="test@example.com",
            password="SecurePass123",
            remember_me=True,
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1"
        )
        
        user = User.create(
            email=dto.email,
            name="Test User",
            password=dto.password
        )
        
        session = UserSession.create(
            user_id=user.id,
            session_token="test_token_123",
            expires_at=datetime.utcnow() + timedelta(hours=720)  # 30 days
        )
        
        self.mock_auth_service.authenticate.return_value = user
        self.mock_auth_service.create_session.return_value = session
        
        with patch.object(self.use_case, '_generate_session_token', return_value="test_token_123"):
            result = self.use_case.login(dto)
        
        assert result.expires_in == 720 * 3600  # 30 days in seconds
        
        # Verify session duration
        create_session_call = self.mock_auth_service.create_session.call_args
        assert create_session_call[1]['duration_hours'] == 720

    def test_login_authentication_failed(self):
        """Test login when authentication fails."""
        dto = LoginDTO(
            email="test@example.com",
            password="WrongPassword",
            remember_me=False
        )
        
        self.mock_auth_service.authenticate.return_value = None
        
        with pytest.raises(ValueError, match="Invalid email or password"):
            self.use_case.login(dto)
        
        # Session should not be created
        self.mock_auth_service.create_session.assert_not_called()

    def test_logout_single_session(self):
        """Test logout of single session."""
        token = "test_token_123"
        dto = LogoutDTO(revoke_all_sessions=False)
        
        user_id = uuid4()
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        self.mock_session_repository.get_by_token.return_value = session
        
        result = self.use_case.logout(token, dto)
        
        assert result is True
        self.mock_session_repository.get_by_token.assert_called_once_with(token)
        self.mock_auth_service.revoke_session.assert_called_once_with(token)
        self.mock_auth_service.revoke_all_user_sessions.assert_not_called()

    def test_logout_all_sessions(self):
        """Test logout of all user sessions."""
        token = "test_token_123"
        dto = LogoutDTO(revoke_all_sessions=True)
        
        user_id = uuid4()
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        self.mock_session_repository.get_by_token.return_value = session
        
        result = self.use_case.logout(token, dto)
        
        assert result is True
        self.mock_auth_service.revoke_all_user_sessions.assert_called_once_with(user_id)
        self.mock_auth_service.revoke_session.assert_not_called()

    def test_logout_session_not_found(self):
        """Test logout when session doesn't exist."""
        token = "nonexistent_token"
        dto = LogoutDTO(revoke_all_sessions=False)
        
        self.mock_session_repository.get_by_token.return_value = None
        
        result = self.use_case.logout(token, dto)
        
        assert result is False

    def test_validate_session_valid(self):
        """Test validating a valid session."""
        token = "test_token_123"
        
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        
        self.mock_auth_service.validate_session.return_value = user
        
        result = self.use_case.validate_session(token)
        
        assert result.email == user.email.value
        self.mock_auth_service.validate_session.assert_called_once_with(token)

    def test_validate_session_invalid(self):
        """Test validating an invalid session."""
        token = "invalid_token"
        
        self.mock_auth_service.validate_session.return_value = None
        
        result = self.use_case.validate_session(token)
        
        assert result is None

    def test_refresh_session_successful(self):
        """Test successful session refresh."""
        token = "old_token"
        new_token = "new_token"
        
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        
        old_session = UserSession.create(
            user_id=user.id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        new_session = UserSession.create(
            user_id=user.id,
            session_token=new_token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.mock_auth_service.validate_session.return_value = user
        self.mock_session_repository.get_by_token.return_value = old_session
        self.mock_auth_service.create_session.return_value = new_session
        
        with patch.object(self.use_case, '_generate_session_token', return_value=new_token):
            result = self.use_case.refresh_session(token)
        
        assert isinstance(result, AuthResponseDTO)
        assert result.access_token == new_token
        
        # Verify old session was revoked
        self.mock_auth_service.revoke_session.assert_called_once_with(token)

    def test_refresh_session_invalid(self):
        """Test refreshing an invalid session."""
        token = "invalid_token"
        
        self.mock_auth_service.validate_session.return_value = None
        
        result = self.use_case.refresh_session(token)
        
        assert result is None

    def test_request_password_reset_user_exists(self):
        """Test password reset request for existing user."""
        dto = PasswordResetRequestDTO(email="test@example.com")
        
        user = User.create(
            email=dto.email,
            name="Test User",
            password="SecurePass123"
        )
        
        self.mock_user_repository.get_by_email.return_value = user
        
        result = self.use_case.request_password_reset(dto)
        
        assert result is True

    def test_request_password_reset_user_not_exists(self):
        """Test password reset request for non-existing user."""
        dto = PasswordResetRequestDTO(email="nonexistent@example.com")
        
        self.mock_user_repository.get_by_email.return_value = None
        
        result = self.use_case.request_password_reset(dto)
        
        # Should return True for security (don't reveal if email exists)
        assert result is True

    def test_request_password_reset_inactive_user(self):
        """Test password reset request for inactive user."""
        dto = PasswordResetRequestDTO(email="test@example.com")
        
        user = User.create(
            email=dto.email,
            name="Test User",
            password="SecurePass123"
        )
        inactive_user = user.deactivate()
        
        self.mock_user_repository.get_by_email.return_value = inactive_user
        
        result = self.use_case.request_password_reset(dto)
        
        # Should return True for security
        assert result is True

    def test_confirm_password_reset_valid_token(self):
        """Test confirming password reset with valid token."""
        dto = PasswordResetConfirmDTO(
            token="valid_reset_token_12345678901234567890",
            new_password="NewSecurePass123"
        )
        
        result = self.use_case.confirm_password_reset(dto)
        
        # This is a placeholder implementation
        assert result is True

    def test_confirm_password_reset_invalid_token(self):
        """Test confirming password reset with invalid token."""
        dto = PasswordResetConfirmDTO(
            token="short",  # Too short
            new_password="NewSecurePass123"
        )
        
        with pytest.raises(ValueError, match="Invalid reset token"):
            self.use_case.confirm_password_reset(dto)

    def test_change_password_with_current_successful(self):
        """Test successful password change with current password."""
        user_id = uuid4()
        current_password = "OldPass123"
        new_password = "NewPass456"
        
        user = User.create(
            email="test@example.com",
            name="Test User",
            password=current_password
        )
        user = user.model_copy(update={"id": user_id})
        
        updated_user = user.change_password(new_password)
        
        self.mock_user_repository.get_by_id.return_value = user
        self.mock_user_repository.save.return_value = updated_user
        
        result = self.use_case.change_password_with_current(
            user_id, current_password, new_password
        )
        
        assert result is True
        self.mock_user_repository.save.assert_called_once()
        self.mock_auth_service.revoke_all_user_sessions.assert_called_once_with(user_id)

    def test_change_password_user_not_found(self):
        """Test password change when user doesn't exist."""
        user_id = uuid4()
        
        self.mock_user_repository.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="User not found"):
            self.use_case.change_password_with_current(
                user_id, "OldPass123", "NewPass456"
            )

    def test_change_password_incorrect_current(self):
        """Test password change with incorrect current password."""
        user_id = uuid4()
        current_password = "CorrectPass123"
        wrong_password = "WrongPass123"
        new_password = "NewPass456"
        
        user = User.create(
            email="test@example.com",
            name="Test User",
            password=current_password
        )
        user = user.model_copy(update={"id": user_id})
        
        self.mock_user_repository.get_by_id.return_value = user
        
        with pytest.raises(ValueError, match="Current password is incorrect"):
            self.use_case.change_password_with_current(
                user_id, wrong_password, new_password
            )

    def test_generate_session_token(self):
        """Test session token generation."""
        token = self.use_case._generate_session_token()
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Generate another token and verify they're different
        token2 = self.use_case._generate_session_token()
        assert token != token2

    def test_generate_reset_token(self):
        """Test reset token generation."""
        token = self.use_case._generate_reset_token()
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Generate another token and verify they're different
        token2 = self.use_case._generate_reset_token()
        assert token != token2

    def test_uow_transaction_management(self):
        """Test that UnitOfWork transactions are properly managed."""
        dto = LoginDTO(
            email="test@example.com",
            password="SecurePass123",
            remember_me=False
        )
        
        user = User.create(
            email=dto.email,
            name="Test User",
            password=dto.password
        )
        
        session = UserSession.create(
            user_id=user.id,
            session_token="test_token_123",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.mock_auth_service.authenticate.return_value = user
        self.mock_auth_service.create_session.return_value = session
        
        with patch.object(self.use_case, '_generate_session_token', return_value="test_token_123"):
            result = self.use_case.login(dto)
        
        # Verify UnitOfWork context manager was used
        self.mock_uow.__enter__.assert_called()
        self.mock_uow.__exit__.assert_called()