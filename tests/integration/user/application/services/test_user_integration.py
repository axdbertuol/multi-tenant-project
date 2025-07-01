import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from user.application.use_cases.user_use_cases import UserUseCase
from user.application.use_cases.auth_use_cases import AuthUseCase
from user.application.use_cases.session_use_cases import SessionUseCase
from user.application.dtos.user_dto import UserCreateDTO, UserUpdateDTO
from user.application.dtos.auth_dto import LoginDTO, LogoutDTO
from user.domain.entities.user import User
from user.domain.entities.user_session import UserSession, SessionStatus
from user.infrastructure.user_unit_of_work import UserUnitOfWork


class TestUserIntegration:
    """Integration tests for user bounded context end-to-end flows."""
    
    def setup_method(self):
        """Set up test fixtures with in-memory repositories."""
        # This would typically use an in-memory database or test database
        # For now, we'll mock the UnitOfWork and repositories
        from unittest.mock import Mock, MagicMock
        
        self.mock_uow = Mock(spec=UserUnitOfWork)
        self.mock_user_repository = Mock()
        self.mock_session_repository = Mock()
        
        def get_repository(name):
            if name == "user":
                return self.mock_user_repository
            elif name == "user_session":
                return self.mock_session_repository
            return None
        
        self.mock_uow.get_repository.side_effect = get_repository
        self.mock_uow.__enter__ = Mock(return_value=self.mock_uow)
        self.mock_uow.__exit__ = Mock(return_value=None)
        
        # Initialize use cases
        self.user_use_case = UserUseCase(self.mock_uow)
        self.auth_use_case = AuthUseCase(self.mock_uow)
        self.session_use_case = SessionUseCase(self.mock_uow)

    def test_complete_user_registration_and_login_flow(self):
        """Test complete flow: register user -> login -> access protected resource."""
        # Step 1: Register new user
        user_dto = UserCreateDTO(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        
        # Mock user creation
        created_user = User.create(
            email=user_dto.email,
            name=user_dto.name,
            password=user_dto.password
        )
        
        # Mock domain service and repository responses
        self.user_use_case._user_domain_service.is_email_available.return_value = True
        self.mock_user_repository.save.return_value = created_user
        
        # Create user
        user_response = self.user_use_case.create_user(user_dto)
        
        assert user_response.email == user_dto.email
        assert user_response.name == user_dto.name
        assert user_response.is_active is True
        
        # Step 2: Login with created user
        login_dto = LoginDTO(
            email=user_dto.email,
            password=user_dto.password,
            remember_me=False,
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1"
        )
        
        # Mock authentication service
        session = UserSession.create(
            user_id=created_user.id,
            session_token="test_session_token",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.auth_use_case._auth_service.authenticate.return_value = created_user
        self.auth_use_case._auth_service.create_session.return_value = session
        
        # Perform login
        auth_response = self.auth_use_case.login(login_dto)
        
        assert auth_response.user.email == user_dto.email
        assert auth_response.access_token == "test_session_token"
        assert auth_response.expires_in == 24 * 3600
        
        # Step 3: Validate session (simulating protected resource access)
        self.auth_use_case._auth_service.validate_session.return_value = created_user
        
        validated_user = self.auth_use_case.validate_session("test_session_token")
        
        assert validated_user.email == user_dto.email
        assert validated_user.is_active is True

    def test_user_profile_update_flow(self):
        """Test user profile update flow."""
        # Create initial user
        user = User.create(
            email="test@example.com",
            name="Original Name",
            password="SecurePass123"
        )
        
        # Mock repository responses
        self.mock_user_repository.get_by_id.return_value = user
        
        # Update user profile
        update_dto = UserUpdateDTO(
            name="Updated Name",
            is_active=True
        )
        
        updated_user = user.update_name(update_dto.name)
        self.mock_user_repository.save.return_value = updated_user
        self.user_use_case._user_domain_service.validate_user_activation.return_value = (True, "Can be activated")
        
        result = self.user_use_case.update_user(user.id, update_dto)
        
        assert result.name == "Updated Name"
        assert result.id == user.id

    def test_password_change_and_session_invalidation_flow(self):
        """Test password change flow that invalidates all sessions."""
        user_id = uuid4()
        old_password = "OldPass123"
        new_password = "NewPass456"
        
        # Create user with old password
        user = User.create(
            email="test@example.com",
            name="Test User",
            password=old_password
        )
        user = user.model_copy(update={"id": user_id})
        
        # Mock repository responses
        self.mock_user_repository.get_by_id.return_value = user
        updated_user = user.change_password(new_password)
        self.mock_user_repository.save.return_value = updated_user
        
        # Change password
        result = self.auth_use_case.change_password_with_current(
            user_id, old_password, new_password
        )
        
        assert result is True
        
        # Verify all sessions were revoked
        self.auth_use_case._auth_service.revoke_all_user_sessions.assert_called_once_with(user_id)

    def test_session_management_flow(self):
        """Test session management: create, extend, revoke."""
        user_id = uuid4()
        
        # Step 1: Create session
        session = UserSession.create(
            user_id=user_id,
            session_token="test_token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        self.mock_session_repository.get_by_token.return_value = session
        
        session_dto = self.session_use_case.get_session_by_token("test_token")
        
        assert session_dto.session_token == "test_token"
        assert session_dto.user_id == user_id
        assert session_dto.is_valid is True
        
        # Step 2: Extend session
        extended_session = session.extend(hours=12)
        self.mock_session_repository.save.return_value = extended_session
        
        extended_dto = self.session_use_case.extend_session("test_token", 12)
        
        assert extended_dto is not None
        
        # Step 3: Revoke session
        revoked_session = session.revoke()
        self.mock_session_repository.save.return_value = revoked_session
        
        result = self.session_use_case.revoke_session("test_token")
        
        assert result is True

    def test_multi_session_user_flow(self):
        """Test user with multiple active sessions."""
        user_id = uuid4()
        
        # Create multiple sessions for same user
        sessions = [
            UserSession.create(
                user_id=user_id,
                session_token=f"token_{i}",
                expires_at=datetime.utcnow() + timedelta(hours=i+1),
                user_agent=f"Browser {i}",
                ip_address=f"192.168.1.{i+1}"
            )
            for i in range(3)
        ]
        
        self.mock_session_repository.get_user_sessions.return_value = sessions
        
        # Get all user sessions
        user_sessions = self.session_use_case.get_user_sessions(user_id)
        
        assert len(user_sessions) == 3
        for i, session_dto in enumerate(user_sessions):
            assert session_dto.session_token == f"token_{i}"
            assert session_dto.user_agent == f"Browser {i}"
        
        # Revoke all sessions
        self.mock_session_repository.revoke_all_user_sessions.return_value = 3
        
        revoked_count = self.session_use_case.revoke_all_user_sessions(user_id)
        
        assert revoked_count == 3

    def test_user_deactivation_and_session_cleanup_flow(self):
        """Test user deactivation with session cleanup."""
        user_id = uuid4()
        
        # Create active user with sessions
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        user = user.model_copy(update={"id": user_id})
        
        # Mock repository responses
        self.mock_user_repository.get_by_id.return_value = user
        deactivated_user = user.deactivate()
        self.mock_user_repository.save.return_value = deactivated_user
        self.user_use_case._user_domain_service.validate_user_deactivation.return_value = (True, "Can be deactivated")
        
        # Deactivate user
        result = self.user_use_case.deactivate_user(user_id)
        
        assert result.is_active is False
        
        # Cleanup sessions (would typically be done by a background job)
        self.mock_session_repository.revoke_all_user_sessions.return_value = 2
        
        revoked_count = self.session_use_case.revoke_all_user_sessions(user_id)
        
        assert revoked_count == 2

    def test_login_with_invalid_credentials_flow(self):
        """Test login attempt with invalid credentials."""
        login_dto = LoginDTO(
            email="test@example.com",
            password="WrongPassword",
            remember_me=False
        )
        
        # Mock authentication failure
        self.auth_use_case._auth_service.authenticate.return_value = None
        
        with pytest.raises(ValueError, match="Invalid email or password"):
            self.auth_use_case.login(login_dto)

    def test_session_expiry_handling_flow(self):
        """Test handling of expired sessions."""
        user_id = uuid4()
        
        # Create expired session
        expired_session = UserSession.create(
            user_id=user_id,
            session_token="expired_token",
            expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired
        )
        
        self.mock_session_repository.get_by_token.return_value = expired_session
        
        # Validate expired session
        self.auth_use_case._auth_service.validate_session.return_value = None
        
        result = self.auth_use_case.validate_session("expired_token")
        
        assert result is None

    def test_email_uniqueness_constraint_flow(self):
        """Test email uniqueness constraint during registration."""
        # First user registration
        user_dto1 = UserCreateDTO(
            email="duplicate@example.com",
            name="First User",
            password="SecurePass123"
        )
        
        # Mock first registration success
        self.user_use_case._user_domain_service.is_email_available.return_value = True
        created_user = User.create(
            email=user_dto1.email,
            name=user_dto1.name,
            password=user_dto1.password
        )
        self.mock_user_repository.save.return_value = created_user
        
        first_user = self.user_use_case.create_user(user_dto1)
        assert first_user.email == user_dto1.email
        
        # Second user registration with same email
        user_dto2 = UserCreateDTO(
            email="duplicate@example.com",  # Same email
            name="Second User",
            password="SecurePass456"
        )
        
        # Mock email not available
        self.user_use_case._user_domain_service.is_email_available.return_value = False
        
        with pytest.raises(ValueError, match="Email duplicate@example.com is already in use"):
            self.user_use_case.create_user(user_dto2)

    def test_remember_me_session_duration_flow(self):
        """Test remember me functionality with extended session duration."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        
        # Login with remember me
        login_dto = LoginDTO(
            email="test@example.com",
            password="SecurePass123",
            remember_me=True
        )
        
        # Mock long-lived session (30 days)
        session = UserSession.create(
            user_id=user.id,
            session_token="long_session_token",
            expires_at=datetime.utcnow() + timedelta(hours=720)  # 30 days
        )
        
        self.auth_use_case._auth_service.authenticate.return_value = user
        self.auth_use_case._auth_service.create_session.return_value = session
        
        auth_response = self.auth_use_case.login(login_dto)
        
        # Verify extended session duration
        assert auth_response.expires_in == 720 * 3600  # 30 days in seconds
        
        # Verify session creation was called with correct duration
        create_session_call = self.auth_use_case._auth_service.create_session.call_args
        assert create_session_call[1]['duration_hours'] == 720