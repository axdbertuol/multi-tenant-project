import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4

from user.domain.services.authentication_service import AuthenticationService
from user.domain.entities.user import User
from user.domain.entities.user_session import UserSession, SessionStatus
from user.domain.value_objects.email import Email


class TestAuthenticationService:
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_uow = Mock()
        self.mock_user_repository = Mock()
        self.mock_session_repository = Mock()
        
        def get_repository(name):
            if name == "user":
                return self.mock_user_repository
            elif name == "user_session":
                return self.mock_session_repository
            return None
        
        self.mock_uow.get_repository.side_effect = get_repository
        
        self.service = AuthenticationService(self.mock_uow)

    def test_authenticate_successful(self):
        """Test successful user authentication."""
        email = "test@example.com"
        password = "Password123"
        
        user = User.create(email=email, name="Test User", password=password)
        self.mock_user_repository.get_by_email.return_value = user
        
        result = self.service.authenticate(email, password)
        
        assert result == user
        self.mock_user_repository.get_by_email.assert_called_once()

    def test_authenticate_user_not_found(self):
        """Test authentication when user doesn't exist."""
        email = "nonexistent@example.com"
        password = "Password123"
        
        self.mock_user_repository.get_by_email.return_value = None
        
        result = self.service.authenticate(email, password)
        
        assert result is None
        self.mock_user_repository.get_by_email.assert_called_once()

    def test_authenticate_inactive_user(self):
        """Test authentication with inactive user."""
        email = "test@example.com"
        password = "Password123"
        
        user = User.create(email=email, name="Test User", password=password)
        inactive_user = user.deactivate()
        self.mock_user_repository.get_by_email.return_value = inactive_user
        
        result = self.service.authenticate(email, password)
        
        assert result is None

    def test_authenticate_wrong_password(self):
        """Test authentication with wrong password."""
        email = "test@example.com"
        correct_password = "Password123"
        wrong_password = "WrongPassword"
        
        user = User.create(email=email, name="Test User", password=correct_password)
        self.mock_user_repository.get_by_email.return_value = user
        
        result = self.service.authenticate(email, wrong_password)
        
        assert result is None

    def test_authenticate_invalid_email_format(self):
        """Test authentication with invalid email format."""
        invalid_email = "not-an-email"
        password = "Password123"
        
        result = self.service.authenticate(invalid_email, password)
        
        assert result is None
        # Repository should not be called with invalid email
        self.mock_user_repository.get_by_email.assert_not_called()

    def test_create_session(self):
        """Test creating a new user session."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="Password123"
        )
        token = "test_token_123"
        duration_hours = 24
        user_agent = "Mozilla/5.0"
        ip_address = "192.168.1.1"
        
        # Mock the session repository save method
        def mock_save(session):
            return session
        
        self.mock_session_repository.save.side_effect = mock_save
        
        result = self.service.create_session(
            user=user,
            token=token,
            duration_hours=duration_hours,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        assert isinstance(result, UserSession)
        assert result.user_id == user.id
        assert result.session_token == token
        assert result.user_agent == user_agent
        assert result.ip_address == ip_address
        assert result.status == SessionStatus.ACTIVE
        
        # Check expiration time is approximately correct
        expected_expires = datetime.utcnow() + timedelta(hours=duration_hours)
        time_diff = abs((result.expires_at - expected_expires).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance
        
        self.mock_session_repository.save.assert_called_once()

    def test_create_session_default_duration(self):
        """Test creating session with default duration."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="Password123"
        )
        token = "test_token_123"
        
        def mock_save(session):
            return session
        
        self.mock_session_repository.save.side_effect = mock_save
        
        result = self.service.create_session(user=user, token=token)
        
        # Check default 24-hour duration
        expected_expires = datetime.utcnow() + timedelta(hours=24)
        time_diff = abs((result.expires_at - expected_expires).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance

    def test_validate_session_valid(self):
        """Test validating a valid session."""
        token = "test_token_123"
        user_id = uuid4()
        
        # Create valid session
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Create active user
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="Password123"
        )
        user = user.model_copy(update={"id": user_id})
        
        self.mock_session_repository.get_by_token.return_value = session
        self.mock_user_repository.get_by_id.return_value = user
        
        result = self.service.validate_session(token)
        
        assert result == user
        self.mock_session_repository.get_by_token.assert_called_once_with(token)
        self.mock_user_repository.get_by_id.assert_called_once_with(user_id)

    def test_validate_session_not_found(self):
        """Test validating non-existent session."""
        token = "nonexistent_token"
        
        self.mock_session_repository.get_by_token.return_value = None
        
        result = self.service.validate_session(token)
        
        assert result is None
        self.mock_session_repository.get_by_token.assert_called_once_with(token)
        self.mock_user_repository.get_by_id.assert_not_called()

    def test_validate_session_expired(self):
        """Test validating expired session."""
        token = "expired_token"
        user_id = uuid4()
        
        # Create expired session
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired
        )
        
        self.mock_session_repository.get_by_token.return_value = session
        
        result = self.service.validate_session(token)
        
        assert result is None
        self.mock_user_repository.get_by_id.assert_not_called()

    def test_validate_session_inactive_user(self):
        """Test validating session for inactive user."""
        token = "test_token_123"
        user_id = uuid4()
        
        # Create valid session
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Create inactive user
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="Password123"
        )
        inactive_user = user.deactivate()
        inactive_user = inactive_user.model_copy(update={"id": user_id})
        
        self.mock_session_repository.get_by_token.return_value = session
        self.mock_user_repository.get_by_id.return_value = inactive_user
        
        result = self.service.validate_session(token)
        
        assert result is None

    def test_validate_session_user_not_found(self):
        """Test validating session when user doesn't exist."""
        token = "test_token_123"
        user_id = uuid4()
        
        # Create valid session
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        self.mock_session_repository.get_by_token.return_value = session
        self.mock_user_repository.get_by_id.return_value = None
        
        result = self.service.validate_session(token)
        
        assert result is None

    def test_revoke_session_successful(self):
        """Test successfully revoking a session."""
        token = "test_token_123"
        user_id = uuid4()
        
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        self.mock_session_repository.get_by_token.return_value = session
        
        result = self.service.revoke_session(token)
        
        assert result is True
        self.mock_session_repository.get_by_token.assert_called_once_with(token)
        self.mock_session_repository.save.assert_called_once()
        
        # Verify the session was revoked
        saved_session = self.mock_session_repository.save.call_args[0][0]
        assert saved_session.status == SessionStatus.REVOKED

    def test_revoke_session_not_found(self):
        """Test revoking non-existent session."""
        token = "nonexistent_token"
        
        self.mock_session_repository.get_by_token.return_value = None
        
        result = self.service.revoke_session(token)
        
        assert result is False
        self.mock_session_repository.get_by_token.assert_called_once_with(token)
        self.mock_session_repository.save.assert_not_called()

    def test_revoke_all_user_sessions(self):
        """Test revoking all sessions for a user."""
        user_id = uuid4()
        expected_count = 3
        
        self.mock_session_repository.revoke_all_user_sessions.return_value = expected_count
        
        result = self.service.revoke_all_user_sessions(user_id)
        
        assert result == expected_count
        self.mock_session_repository.revoke_all_user_sessions.assert_called_once_with(user_id)

    def test_service_uses_correct_repositories(self):
        """Test that service uses the correct repositories from UnitOfWork."""
        expected_calls = [
            ("user",),
            ("user_session",)
        ]
        
        actual_calls = [call[0] for call in self.mock_uow.get_repository.call_args_list]
        
        assert actual_calls == expected_calls
        assert self.service._user_repository == self.mock_user_repository
        assert self.service._session_repository == self.mock_session_repository

    def test_authenticate_email_case_sensitivity(self):
        """Test authentication with different email cases."""
        original_email = "Test@Example.com"
        login_email = "test@example.com"
        password = "Password123"
        
        user = User.create(email=original_email, name="Test User", password=password)
        
        def mock_get_by_email(email_vo):
            # Email should be normalized to lowercase
            if email_vo.value == "test@example.com":
                return user
            return None
        
        self.mock_user_repository.get_by_email.side_effect = mock_get_by_email
        
        result = self.service.authenticate(login_email, password)
        
        assert result == user