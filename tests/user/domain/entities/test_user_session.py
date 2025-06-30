import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from user.domain.entities.user_session import UserSession, SessionStatus


class TestUserSession:
    def test_create_session(self):
        """Test creating a new user session."""
        user_id = uuid4()
        token = "test_token_123"
        expires_at = datetime.utcnow() + timedelta(hours=24)
        metadata = {"browser": "Chrome"}
        ip_address = "192.168.1.1"
        user_agent = "Mozilla/5.0"
        
        session = UserSession.create(
            user_id=user_id,
            session_token=token,
            expires_at=expires_at,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        assert isinstance(session.id, UUID)
        assert session.user_id == user_id
        assert session.session_token == token
        assert session.status == SessionStatus.ACTIVE
        assert session.expires_at == expires_at
        assert session.metadata == metadata
        assert session.ip_address == ip_address
        assert session.user_agent == user_agent
        assert isinstance(session.login_at, datetime)
        assert isinstance(session.created_at, datetime)
        assert session.logout_at is None
        assert session.updated_at is None

    def test_logout_session(self):
        """Test logging out a session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        logged_out_session = session.logout()
        
        assert logged_out_session.status == SessionStatus.LOGGED_OUT
        assert logged_out_session.logout_at is not None
        assert logged_out_session.updated_at is not None
        assert logged_out_session.id == session.id

    def test_expire_session(self):
        """Test expiring a session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        expired_session = session.expire()
        
        assert expired_session.status == SessionStatus.EXPIRED
        assert expired_session.updated_at is not None
        assert expired_session.id == session.id

    def test_revoke_session(self):
        """Test revoking a session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        revoked_session = session.revoke()
        
        assert revoked_session.status == SessionStatus.REVOKED
        assert revoked_session.logout_at is not None
        assert revoked_session.updated_at is not None
        assert revoked_session.id == session.id

    def test_is_active_with_valid_session(self):
        """Test is_active for a valid session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        assert session.is_active() is True

    def test_is_active_with_expired_session(self):
        """Test is_active for an expired session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        assert session.is_active() is False

    def test_is_active_with_logged_out_session(self):
        """Test is_active for a logged out session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        logged_out_session = session.logout()
        assert logged_out_session.is_active() is False

    def test_is_expired(self):
        """Test is_expired method."""
        user_id = uuid4()
        
        # Future expiration
        future_expires = datetime.utcnow() + timedelta(hours=24)
        active_session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=future_expires
        )
        assert active_session.is_expired() is False
        
        # Past expiration
        past_expires = datetime.utcnow() - timedelta(hours=1)
        expired_session = UserSession.create(
            user_id=user_id,
            session_token="token456",
            expires_at=past_expires
        )
        assert expired_session.is_expired() is True

    def test_is_valid(self):
        """Test is_valid method."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        # Valid session
        assert session.is_valid() is True
        
        # Invalid after logout
        logged_out_session = session.logout()
        assert logged_out_session.is_valid() is False

    def test_get_session_duration_active_session(self):
        """Test get_session_duration for active session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        # Active session should return None
        assert session.get_session_duration() is None

    def test_get_session_duration_logged_out_session(self):
        """Test get_session_duration for logged out session."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        # Wait a bit then logout
        import time
        time.sleep(0.1)
        logged_out_session = session.logout()
        
        duration = logged_out_session.get_session_duration()
        assert duration is not None
        assert duration >= 0

    def test_extend_session(self):
        """Test extending session expiration."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        new_expires_at = datetime.utcnow() + timedelta(hours=24)
        extended_session = session.extend_session(new_expires_at)
        
        assert extended_session.expires_at == new_expires_at
        assert extended_session.updated_at is not None
        assert extended_session.id == session.id

    def test_extend_session_by_hours(self):
        """Test extending session by hours."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        extended_session = session.extend(hours=12)
        
        # Check that expiration is roughly 12 hours from now
        expected_expires = datetime.utcnow() + timedelta(hours=12)
        time_diff = abs((extended_session.expires_at - expected_expires).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance

    def test_extend_inactive_session_raises_error(self):
        """Test that extending inactive session raises error."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        logged_out_session = session.logout()
        
        with pytest.raises(ValueError, match="Cannot extend inactive session"):
            logged_out_session.extend_session(datetime.utcnow() + timedelta(hours=1))

    def test_session_immutability(self):
        """Test that session operations return new instances."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at
        )
        
        logged_out_session = session.logout()
        
        # Original session should be unchanged
        assert session.status == SessionStatus.ACTIVE
        assert session.logout_at is None
        
        # Logged out session should have changes
        assert logged_out_session.status == SessionStatus.LOGGED_OUT
        assert logged_out_session.logout_at is not None
        
        # Should be different instances
        assert session is not logged_out_session

    def test_session_metadata_handling(self):
        """Test session metadata handling."""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        metadata = {
            "browser": "Chrome",
            "version": "91.0",
            "device": "desktop"
        }
        
        session = UserSession.create(
            user_id=user_id,
            session_token="token123",
            expires_at=expires_at,
            metadata=metadata
        )
        
        assert session.metadata == metadata
        
        # Test with None metadata
        session_no_metadata = UserSession.create(
            user_id=user_id,
            session_token="token456",
            expires_at=expires_at
        )
        
        assert session_no_metadata.metadata is None