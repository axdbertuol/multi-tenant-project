import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from uuid import uuid4

from user.application.use_cases.session_use_cases import SessionUseCase
from user.application.dtos.session_dto import SessionResponseDTO
from user.domain.entities.user import User
from user.domain.entities.user_session import UserSession, SessionStatus


class TestSessionUseCase:
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_uow = Mock()
        self.mock_session_repository = Mock()
        
        self.mock_uow.get_repository.return_value = self.mock_session_repository
        self.mock_uow.__enter__ = Mock(return_value=self.mock_uow)
        self.mock_uow.__exit__ = Mock(return_value=None)
        
        self.use_case = SessionUseCase(self.mock_uow)

    def test_get_session_by_token_found(self):
        """Test getting session by token when session exists."""
        token = "test_token_123"
        user_id = uuid4()
        
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        self.mock_session_repository.get_by_token.return_value = session
        
        result = self.use_case.get_session_by_token(token)
        
        assert isinstance(result, SessionResponseDTO)
        assert result.session_token == token
        assert result.user_id == user_id
        assert result.is_valid is True
        assert result.is_expired is False
        
        self.mock_session_repository.get_by_token.assert_called_once_with(token)

    def test_get_session_by_token_not_found(self):
        """Test getting session by token when session doesn't exist."""
        token = "nonexistent_token"
        
        self.mock_session_repository.get_by_token.return_value = None
        
        result = self.use_case.get_session_by_token(token)
        
        assert result is None
        self.mock_session_repository.get_by_token.assert_called_once_with(token)

    def test_get_user_sessions(self):
        """Test getting all sessions for a user."""
        user_id = uuid4()
        
        sessions = [
            UserSession.create(
                user_id=user_id,
                session_token=f"token_{i}",
                expires_at=datetime.utcnow() + timedelta(hours=i+1)
            )
            for i in range(3)
        ]
        
        self.mock_session_repository.get_user_sessions.return_value = sessions
        
        result = self.use_case.get_user_sessions(user_id)
        
        assert len(result) == 3
        for i, session_dto in enumerate(result):
            assert isinstance(session_dto, SessionResponseDTO)
            assert session_dto.user_id == user_id
            assert session_dto.session_token == f"token_{i}"
        
        self.mock_session_repository.get_user_sessions.assert_called_once_with(user_id)

    def test_get_active_user_sessions(self):
        """Test getting only active sessions for a user."""
        user_id = uuid4()
        
        # Create mix of active and inactive sessions
        active_session = UserSession.create(
            user_id=user_id,
            session_token="active_token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        expired_session = UserSession.create(
            user_id=user_id,
            session_token="expired_token",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        logged_out_session = UserSession.create(
            user_id=user_id,
            session_token="logged_out_token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        ).logout()
        
        all_sessions = [active_session, expired_session, logged_out_session]
        self.mock_session_repository.get_user_sessions.return_value = all_sessions
        
        result = self.use_case.get_active_user_sessions(user_id)
        
        # Should only return active session
        assert len(result) == 1
        assert result[0].session_token == "active_token"
        assert result[0].is_valid is True

    def test_revoke_session_successful(self):
        """Test successfully revoking a session."""
        token = "test_token_123"
        user_id = uuid4()
        
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        revoked_session = session.revoke()
        
        self.mock_session_repository.get_by_token.return_value = session
        self.mock_session_repository.save.return_value = revoked_session
        
        result = self.use_case.revoke_session(token)
        
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
        
        result = self.use_case.revoke_session(token)
        
        assert result is False
        self.mock_session_repository.save.assert_not_called()

    def test_revoke_all_user_sessions(self):
        """Test revoking all sessions for a user."""
        user_id = uuid4()
        expected_revoked_count = 3
        
        self.mock_session_repository.revoke_all_user_sessions.return_value = expected_revoked_count
        
        result = self.use_case.revoke_all_user_sessions(user_id)
        
        assert result == expected_revoked_count
        self.mock_session_repository.revoke_all_user_sessions.assert_called_once_with(user_id)

    def test_extend_session_successful(self):
        """Test successfully extending a session."""
        token = "test_token_123"
        user_id = uuid4()
        additional_hours = 12
        
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        extended_session = session.extend(additional_hours)
        
        self.mock_session_repository.get_by_token.return_value = session
        self.mock_session_repository.save.return_value = extended_session
        
        result = self.use_case.extend_session(token, additional_hours)
        
        assert isinstance(result, SessionResponseDTO)
        self.mock_session_repository.get_by_token.assert_called_once_with(token)
        self.mock_session_repository.save.assert_called_once()
        
        # Verify the session was extended
        saved_session = self.mock_session_repository.save.call_args[0][0]
        expected_expires = datetime.utcnow() + timedelta(hours=additional_hours)
        time_diff = abs((saved_session.expires_at - expected_expires).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance

    def test_extend_session_not_found(self):
        """Test extending non-existent session."""
        token = "nonexistent_token"
        
        self.mock_session_repository.get_by_token.return_value = None
        
        result = self.use_case.extend_session(token, 12)
        
        assert result is None
        self.mock_session_repository.save.assert_not_called()

    def test_extend_inactive_session(self):
        """Test extending inactive session."""
        token = "logged_out_token"
        user_id = uuid4()
        
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        logged_out_session = session.logout()
        
        self.mock_session_repository.get_by_token.return_value = logged_out_session
        
        with pytest.raises(ValueError, match="Cannot extend inactive session"):
            self.use_case.extend_session(token, 12)

    def test_get_session_count_by_user(self):
        """Test getting session count for a user."""
        user_id = uuid4()
        expected_count = 5
        
        self.mock_session_repository.count_user_sessions.return_value = expected_count
        
        result = self.use_case.get_session_count_by_user(user_id)
        
        assert result == expected_count
        self.mock_session_repository.count_user_sessions.assert_called_once_with(user_id)

    def test_get_session_statistics(self):
        """Test getting session statistics."""
        user_id = uuid4()
        
        # Mock different counts
        self.mock_session_repository.count_user_sessions.return_value = 10
        self.mock_session_repository.count_active_user_sessions.return_value = 3
        
        stats = self.use_case.get_session_statistics(user_id)
        
        assert stats["total_sessions"] == 10
        assert stats["active_sessions"] == 3
        assert stats["inactive_sessions"] == 7
        
        self.mock_session_repository.count_user_sessions.assert_called_once_with(user_id)
        self.mock_session_repository.count_active_user_sessions.assert_called_once_with(user_id)

    def test_cleanup_expired_sessions(self):
        """Test cleaning up expired sessions."""
        expected_cleaned_count = 15
        
        self.mock_session_repository.delete_expired_sessions.return_value = expected_cleaned_count
        
        result = self.use_case.cleanup_expired_sessions()
        
        assert result == expected_cleaned_count
        self.mock_session_repository.delete_expired_sessions.assert_called_once()

    def test_is_session_valid(self):
        """Test checking if session is valid."""
        token = "test_token_123"
        user_id = uuid4()
        
        # Test with valid session
        valid_session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        self.mock_session_repository.get_by_token.return_value = valid_session
        
        result = self.use_case.is_session_valid(token)
        
        assert result is True
        
        # Test with invalid session
        invalid_session = valid_session.logout()
        self.mock_session_repository.get_by_token.return_value = invalid_session
        
        result = self.use_case.is_session_valid(token)
        
        assert result is False
        
        # Test with non-existent session
        self.mock_session_repository.get_by_token.return_value = None
        
        result = self.use_case.is_session_valid(token)
        
        assert result is False

    def test_session_dto_conversion(self):
        """Test that sessions are properly converted to DTOs."""
        user_id = uuid4()
        token = "test_token_123"
        
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        self.mock_session_repository.get_by_token.return_value = session
        
        result = self.use_case.get_session_by_token(token)
        
        assert isinstance(result, SessionResponseDTO)
        assert result.id == session.id
        assert result.user_id == session.user_id
        assert result.session_token == session.session_token
        assert result.status == session.status.value
        assert result.ip_address == session.ip_address
        assert result.user_agent == session.user_agent
        assert result.is_valid == session.is_valid()
        assert result.is_expired == session.is_expired()

    def test_uow_transaction_management(self):
        """Test that UnitOfWork transactions are properly managed for write operations."""
        token = "test_token_123"
        user_id = uuid4()
        
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        self.mock_session_repository.get_by_token.return_value = session
        
        result = self.use_case.revoke_session(token)
        
        # Verify UnitOfWork context manager was used
        self.mock_uow.__enter__.assert_called()
        self.mock_uow.__exit__.assert_called()