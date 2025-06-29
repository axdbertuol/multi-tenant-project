import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from src.domain.entities.user_session import UserSession, SessionStatus
from src.infrastructure.repositories.user_session_repository_impl import UserSessionRepositoryImpl
from tests.factories.session_factory import UserSessionFactory


@pytest.mark.integration
class TestUserSessionRepositoryImpl:
    """Integration tests for UserSessionRepositoryImpl."""
    
    @pytest.fixture
    def session_repository(self, db_session):
        """Create UserSessionRepositoryImpl instance with test database session."""
        return UserSessionRepositoryImpl(db_session)
    
    @pytest.mark.io
     def test_create_session(self, session_repository):
        """Test creating a session in the database."""
        # Arrange
        user_id = uuid4()
        session = UserSessionFactory.create_session(
            user_id=user_id,
            session_token="test_token_123",
            ip_address="192.168.1.1",
            user_agent="Test Agent/1.0"
        )
        
        # Act
        created_session =  session_repository.create(session)
        
        # Assert
        assert created_session.id == session.id
        assert created_session.user_id == user_id
        assert created_session.session_token == "test_token_123"
        assert created_session.status == SessionStatus.ACTIVE
        assert created_session.ip_address == "192.168.1.1"
        assert created_session.user_agent == "Test Agent/1.0"
    
    @pytest.mark.io
     def test_get_by_session_token(self, session_repository):
        """Test getting session by token."""
        # Arrange
        session = UserSessionFactory.create_session(session_token="unique_token_123")
         session_repository.create(session)
        
        # Act
        retrieved_session =  session_repository.get_by_session_token("unique_token_123")
        
        # Assert
        assert retrieved_session is not None
        assert retrieved_session.session_token == "unique_token_123"
        assert retrieved_session.id == session.id
    
    @pytest.mark.io
     def test_get_by_session_token_not_found(self, session_repository):
        """Test getting session by non-existent token."""
        # Act
        result =  session_repository.get_by_session_token("non_existent_token")
        
        # Assert
        assert result is None
    
    @pytest.mark.io
     def test_get_active_sessions_by_user_id(self, session_repository):
        """Test getting active sessions for a user."""
        # Arrange
        user_id = uuid4()
        
        # Create multiple sessions
        active_session1 = UserSessionFactory.create_active_session(user_id=user_id)
        active_session2 = UserSessionFactory.create_active_session(user_id=user_id)
        logged_out_session = UserSessionFactory.create_logged_out_session(user_id=user_id)
        expired_session = UserSessionFactory.create_expired_session(user_id=user_id)
        
         session_repository.create(active_session1)
         session_repository.create(active_session2)
         session_repository.create(logged_out_session)
         session_repository.create(expired_session)
        
        # Act
        active_sessions =  session_repository.get_active_sessions_by_user_id(user_id)
        
        # Assert
        assert len(active_sessions) == 2
        session_ids = [s.id for s in active_sessions]
        assert active_session1.id in session_ids
        assert active_session2.id in session_ids
        assert logged_out_session.id not in session_ids
        assert expired_session.id not in session_ids
    
    @pytest.mark.io
     def test_get_all_sessions_by_user_id(self, session_repository):
        """Test getting all sessions for a user."""
        # Arrange
        user_id = uuid4()
        other_user_id = uuid4()
        
        # Create sessions for target user
        session1 = UserSessionFactory.create_session(user_id=user_id)
        session2 = UserSessionFactory.create_logged_out_session(user_id=user_id)
        session3 = UserSessionFactory.create_expired_session(user_id=user_id)
        
        # Create session for other user
        other_session = UserSessionFactory.create_session(user_id=other_user_id)
        
         session_repository.create(session1)
         session_repository.create(session2)
         session_repository.create(session3)
         session_repository.create(other_session)
        
        # Act
        user_sessions =  session_repository.get_all_sessions_by_user_id(user_id)
        
        # Assert
        assert len(user_sessions) == 3
        session_ids = [s.id for s in user_sessions]
        assert session1.id in session_ids
        assert session2.id in session_ids
        assert session3.id in session_ids
        assert other_session.id not in session_ids
    
    @pytest.mark.io
     def test_update_session(self, session_repository):
        """Test updating a session."""
        # Arrange
        session = UserSessionFactory.create_active_session()
        created_session =  session_repository.create(session)
        
        # Logout the session
        logged_out_session = created_session.logout()
        
        # Act
        updated_session =  session_repository.update(logged_out_session)
        
        # Assert
        assert updated_session.status == SessionStatus.LOGGED_OUT
        assert updated_session.logout_at is not None
        assert updated_session.updated_at is not None
        
        # Verify in database
        retrieved_session =  session_repository.get_by_id(created_session.id)
        assert retrieved_session.status == SessionStatus.LOGGED_OUT
    
    @pytest.mark.io
     def test_expire_sessions_by_user_id(self, session_repository):
        """Test expiring all active sessions for a user."""
        # Arrange
        user_id = uuid4()
        other_user_id = uuid4()
        
        # Create active sessions for target user
        active_session1 = UserSessionFactory.create_active_session(user_id=user_id)
        active_session2 = UserSessionFactory.create_active_session(user_id=user_id)
        
        # Create session for other user
        other_session = UserSessionFactory.create_active_session(user_id=other_user_id)
        
        # Create already logged out session
        logged_out_session = UserSessionFactory.create_logged_out_session(user_id=user_id)
        
         session_repository.create(active_session1)
         session_repository.create(active_session2)
         session_repository.create(other_session)
         session_repository.create(logged_out_session)
        
        # Act
        expired_count =  session_repository.expire_sessions_by_user_id(user_id)
        
        # Assert
        assert expired_count == 2
        
        # Verify sessions are expired
        session1 =  session_repository.get_by_id(active_session1.id)
        session2 =  session_repository.get_by_id(active_session2.id)
        other =  session_repository.get_by_id(other_session.id)
        logged_out =  session_repository.get_by_id(logged_out_session.id)
        
        assert session1.status == SessionStatus.EXPIRED
        assert session2.status == SessionStatus.EXPIRED
        assert other.status == SessionStatus.ACTIVE  # Other user unaffected
        assert logged_out.status == SessionStatus.LOGGED_OUT  # Already logged out
    
    @pytest.mark.io
     def test_cleanup_expired_sessions(self, session_repository):
        """Test cleaning up expired sessions based on expires_at timestamp."""
        # Arrange
        now = datetime.utcnow()
        
        # Create sessions with different expiration times
        active_session = UserSessionFactory.create_session(
            expires_at=now + timedelta(hours=1)  # Future expiration
        )
        
        expired_session1 = UserSessionFactory.create_session(
            expires_at=now - timedelta(hours=1)  # Past expiration
        )
        
        expired_session2 = UserSessionFactory.create_session(
            expires_at=now - timedelta(minutes=30)  # Past expiration
        )
        
        # Create already logged out session (should not be affected)
        logged_out_session = UserSessionFactory.create_logged_out_session(
            expires_at=now - timedelta(hours=2)
        )
        
         session_repository.create(active_session)
         session_repository.create(expired_session1)
         session_repository.create(expired_session2)
         session_repository.create(logged_out_session)
        
        # Act
        cleaned_count =  session_repository.cleanup_expired_sessions()
        
        # Assert
        assert cleaned_count == 2
        
        # Verify sessions are marked as expired
        active =  session_repository.get_by_id(active_session.id)
        expired1 =  session_repository.get_by_id(expired_session1.id)
        expired2 =  session_repository.get_by_id(expired_session2.id)
        logged_out =  session_repository.get_by_id(logged_out_session.id)
        
        assert active.status == SessionStatus.ACTIVE
        assert expired1.status == SessionStatus.EXPIRED
        assert expired2.status == SessionStatus.EXPIRED
        assert logged_out.status == SessionStatus.LOGGED_OUT  # Unchanged
    
    @pytest.mark.io
     def test_session_token_uniqueness(self, session_repository):
        """Test that session token uniqueness is enforced."""
        # Arrange
        session1 = UserSessionFactory.create_session(session_token="duplicate_token")
        session2 = UserSessionFactory.create_session(session_token="duplicate_token")
        
        # Act
         session_repository.create(session1)
        
        # Assert - Second session with same token should fail
        with pytest.raises(Exception):  # Database integrity error
             session_repository.create(session2)
    
    @pytest.mark.io
     def test_delete_session(self, session_repository):
        """Test deleting a session."""
        # Arrange
        session = UserSessionFactory.create_session()
        created_session =  session_repository.create(session)
        
        # Act
        result =  session_repository.delete(created_session.id)
        
        # Assert
        assert result is True
        
        # Verify session is deleted
        deleted_session =  session_repository.get_by_id(created_session.id)
        assert deleted_session is None
    
    @pytest.mark.io
     def test_session_timestamps(self, session_repository):
        """Test that session timestamps are properly handled."""
        # Arrange
        session = UserSessionFactory.create_session()
        
        # Act
        created_session =  session_repository.create(session)
        
        # Assert
        assert created_session.login_at is not None
        assert created_session.created_at is not None
        assert created_session.logout_at is None
        assert created_session.updated_at is None
        
        # Update session and check updated_at
        logged_out_session = created_session.logout()
        result =  session_repository.update(logged_out_session)
        
        assert result.logout_at is not None
        assert result.updated_at is not None
        assert result.updated_at > result.created_at
    
    @pytest.mark.io
     def test_domain_model_mapping(self, session_repository):
        """Test that domain entities are properly mapped to/from database models."""
        # Arrange
        user_id = uuid4()
        session = UserSessionFactory.create_session(
            user_id=user_id,
            session_token="mapping_test_token",
            ip_address="10.0.0.1",
            user_agent="Test Browser/1.0"
        )
        
        # Act - Create and retrieve
        created_session =  session_repository.create(session)
        retrieved_session =  session_repository.get_by_id(created_session.id)
        
        # Assert - All domain properties preserved
        assert isinstance(retrieved_session, UserSession)
        assert retrieved_session.id == session.id
        assert retrieved_session.user_id == user_id
        assert retrieved_session.session_token == "mapping_test_token"
        assert retrieved_session.status == SessionStatus.ACTIVE
        assert retrieved_session.ip_address == "10.0.0.1"
        assert retrieved_session.user_agent == "Test Browser/1.0"
        assert retrieved_session.login_at == created_session.login_at
        assert retrieved_session.expires_at == session.expires_at