import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from user.domain.entities.user_session import UserSession, SessionStatus


class TestUserSession:
    """Unit tests for UserSession domain entity."""

    def test_create_session(self):
        """Test creating a new user session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        session = UserSession.create(
            user_id=user_id,
            session_token="test_token",
            expires_at=expires_at,
            ip_address="192.168.1.1",
            user_agent="Test Agent",
        )

        assert isinstance(session.id, UUID)
        assert session.user_id == user_id
        assert session.session_token == "test_token"
        assert session.status == SessionStatus.ACTIVE
        assert isinstance(session.login_at, datetime)
        assert session.logout_at is None
        assert session.expires_at == expires_at
        assert session.ip_address == "192.168.1.1"
        assert session.user_agent == "Test Agent"
        assert isinstance(session.created_at, datetime)
        assert session.updated_at is None

    def test_create_session_minimal(self):
        """Test creating session with minimal required data."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        assert session.user_id == user_id
        assert session.session_token == "test_token"
        assert session.expires_at == expires_at
        assert session.ip_address is None
        assert session.user_agent is None

    def test_logout_session(self):
        """Test logging out a session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        logged_out_session = session.logout()

        # Original session unchanged
        assert session.status == SessionStatus.ACTIVE
        assert session.logout_at is None
        assert session.updated_at is None

        # New session object with changes
        assert logged_out_session.status == SessionStatus.LOGGED_OUT
        assert logged_out_session.logout_at is not None
        assert logged_out_session.updated_at is not None
        assert logged_out_session.id == session.id

    def test_expire_session(self):
        """Test expiring a session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        expired_session = session.expire()

        # Original session unchanged
        assert session.status == SessionStatus.ACTIVE
        assert session.updated_at is None

        # New session object with changes
        assert expired_session.status == SessionStatus.EXPIRED
        assert expired_session.updated_at is not None
        assert expired_session.id == session.id

    def test_revoke_session(self):
        """Test revoking a session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        revoked_session = session.revoke()

        # Original session unchanged
        assert session.status == SessionStatus.ACTIVE
        assert session.logout_at is None

        # New session object with changes
        assert revoked_session.status == SessionStatus.REVOKED
        assert revoked_session.logout_at is not None
        assert revoked_session.updated_at is not None
        assert revoked_session.id == session.id

    def test_is_active_true(self):
        """Test is_active returns True for active non-expired session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        assert session.is_active() is True

    def test_is_active_false_logged_out(self):
        """Test is_active returns False for logged out session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        logged_out_session = session.logout()
        assert logged_out_session.is_active() is False

    def test_is_active_false_expired_time(self):
        """Test is_active returns False for time-expired session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        assert session.is_active() is False

    def test_is_expired_true(self):
        """Test is_expired returns True for expired session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        assert session.is_expired() is True

    def test_is_expired_false(self):
        """Test is_expired returns False for non-expired session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)  # Not expired

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        assert session.is_expired() is False

    def test_get_session_duration_active(self):
        """Test get_session_duration returns None for active session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        assert session.get_session_duration() is None

    def test_get_session_duration_logged_out(self):
        """Test get_session_duration returns duration for logged out session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        # Wait a bit to ensure measurable duration
        import time

        time.sleep(0.001)

        logged_out_session = session.logout()
        duration = logged_out_session.get_session_duration()

        assert duration is not None
        assert duration > 0
        assert isinstance(duration, int)

    def test_extend_session(self):
        """Test extending session expiration."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        new_expires_at = datetime.utcnow() + timedelta(hours=2)
        extended_session = session.extend_session(new_expires_at)

        # Original session unchanged
        assert session.expires_at == expires_at
        assert session.updated_at is None

        # New session object with changes
        assert extended_session.expires_at == new_expires_at
        assert extended_session.updated_at is not None
        assert extended_session.id == session.id

    def test_extend_session_inactive_raises_error(self):
        """Test extending inactive session raises error."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        logged_out_session = session.logout()
        new_expires_at = datetime.utcnow() + timedelta(hours=2)

        with pytest.raises(ValueError, match="Cannot extend inactive session"):
            logged_out_session.extend_session(new_expires_at)

    def test_session_immutability(self):
        """Test that session entity is immutable."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )

        # Should not be able to directly modify attributes
        with pytest.raises(AttributeError):
            session.status = SessionStatus.LOGGED_OUT

        with pytest.raises(AttributeError):
            session.logout_at = datetime.utcnow()

    def test_session_timestamps(self):
        """Test session creation timestamps."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        before_creation = datetime.utcnow()
        session = UserSession.create(
            user_id=user_id, session_token="test_token", expires_at=expires_at
        )
        after_creation = datetime.utcnow()

        assert before_creation <= session.login_at <= after_creation
        assert before_creation <= session.created_at <= after_creation
        assert session.updated_at is None

    def test_session_status_enum(self):
        """Test session status enum values."""
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.EXPIRED == "expired"
        assert SessionStatus.LOGGED_OUT == "logged_out"
        assert SessionStatus.REVOKED == "revoked"
