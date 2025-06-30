import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from user.infrastructure.repositories.sqlalchemy_user_session_repository import SqlAlchemyUserSessionRepository
from user.infrastructure.database.models import UserSessionModel
from user.domain.entities.user_session import UserSession, SessionStatus


class TestSqlAlchemyUserSessionRepository:
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.repository = SqlAlchemyUserSessionRepository(self.mock_session)

    def test_save_new_session(self):
        """Test saving a new session."""
        user_id = uuid4()
        session = UserSession.create(
            user_id=user_id,
            session_token="test_token_123",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        # Mock session behavior
        self.mock_session.merge.return_value = Mock()
        self.mock_session.commit.return_value = None
        
        result = self.repository.save(session)
        
        assert result == session
        self.mock_session.merge.assert_called_once()
        self.mock_session.commit.assert_called_once()
        
        # Verify the model was created correctly
        merge_call_args = self.mock_session.merge.call_args[0][0]
        assert isinstance(merge_call_args, UserSessionModel)
        assert merge_call_args.session_token == session.session_token

    def test_save_existing_session(self):
        """Test saving an existing session (update)."""
        session_id = uuid4()
        user_id = uuid4()
        
        session = UserSession.create(
            user_id=user_id,
            session_token="test_token_123",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        session = session.model_copy(update={"id": session_id})
        
        self.mock_session.merge.return_value = Mock()
        self.mock_session.commit.return_value = None
        
        result = self.repository.save(session)
        
        assert result == session
        self.mock_session.merge.assert_called_once()
        self.mock_session.commit.assert_called_once()

    def test_save_integrity_error(self):
        """Test saving session with integrity constraint violation."""
        user_id = uuid4()
        session = UserSession.create(
            user_id=user_id,
            session_token="duplicate_token",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.mock_session.merge.side_effect = IntegrityError("", "", "")
        
        with pytest.raises(ValueError, match="Session token already exists"):
            self.repository.save(session)
        
        self.mock_session.rollback.assert_called_once()

    def test_get_by_id_found(self):
        """Test getting session by ID when session exists."""
        session_id = uuid4()
        user_id = uuid4()
        
        # Mock database model
        mock_session_model = Mock(spec=UserSessionModel)
        mock_session_model.id = session_id
        mock_session_model.user_id = user_id
        mock_session_model.session_token = "test_token_123"
        mock_session_model.status = SessionStatus.ACTIVE.value
        mock_session_model.login_at = datetime.utcnow()
        mock_session_model.logout_at = None
        mock_session_model.expires_at = datetime.utcnow() + timedelta(hours=24)
        mock_session_model.metadata = {"browser": "Chrome"}
        mock_session_model.ip_address = "192.168.1.1"
        mock_session_model.user_agent = "Mozilla/5.0"
        mock_session_model.created_at = datetime.utcnow()
        mock_session_model.updated_at = None
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_session_model
        
        result = self.repository.get_by_id(session_id)
        
        assert isinstance(result, UserSession)
        assert result.id == session_id
        assert result.user_id == user_id
        assert result.session_token == "test_token_123"
        
        self.mock_session.query.assert_called_once_with(UserSessionModel)

    def test_get_by_id_not_found(self):
        """Test getting session by ID when session doesn't exist."""
        session_id = uuid4()
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = self.repository.get_by_id(session_id)
        
        assert result is None

    def test_get_by_token_found(self):
        """Test getting session by token when session exists."""
        token = "test_token_123"
        session_id = uuid4()
        user_id = uuid4()
        
        mock_session_model = Mock(spec=UserSessionModel)
        mock_session_model.id = session_id
        mock_session_model.user_id = user_id
        mock_session_model.session_token = token
        mock_session_model.status = SessionStatus.ACTIVE.value
        mock_session_model.login_at = datetime.utcnow()
        mock_session_model.logout_at = None
        mock_session_model.expires_at = datetime.utcnow() + timedelta(hours=24)
        mock_session_model.metadata = None
        mock_session_model.ip_address = None
        mock_session_model.user_agent = None
        mock_session_model.created_at = datetime.utcnow()
        mock_session_model.updated_at = None
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_session_model
        
        result = self.repository.get_by_token(token)
        
        assert isinstance(result, UserSession)
        assert result.session_token == token
        assert result.user_id == user_id

    def test_get_by_token_not_found(self):
        """Test getting session by token when session doesn't exist."""
        token = "nonexistent_token"
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = self.repository.get_by_token(token)
        
        assert result is None

    def test_get_user_sessions(self):
        """Test getting all sessions for a user."""
        user_id = uuid4()
        
        # Mock session models
        mock_sessions = []
        for i in range(3):
            mock_session = Mock(spec=UserSessionModel)
            mock_session.id = uuid4()
            mock_session.user_id = user_id
            mock_session.session_token = f"token_{i}"
            mock_session.status = SessionStatus.ACTIVE.value
            mock_session.login_at = datetime.utcnow()
            mock_session.logout_at = None
            mock_session.expires_at = datetime.utcnow() + timedelta(hours=24)
            mock_session.metadata = None
            mock_session.ip_address = None
            mock_session.user_agent = None
            mock_session.created_at = datetime.utcnow()
            mock_session.updated_at = None
            mock_sessions.append(mock_session)
        
        query_mock = self.mock_session.query.return_value
        query_mock.filter.return_value.order_by.return_value.all.return_value = mock_sessions
        
        result = self.repository.get_user_sessions(user_id)
        
        assert len(result) == 3
        for i, session in enumerate(result):
            assert isinstance(session, UserSession)
            assert session.user_id == user_id
            assert session.session_token == f"token_{i}"
        
        self.mock_session.query.assert_called_once_with(UserSessionModel)

    def test_revoke_all_user_sessions(self):
        """Test revoking all sessions for a user."""
        user_id = uuid4()
        expected_count = 5
        
        # Mock the update query
        query_mock = self.mock_session.query.return_value
        query_mock.filter.return_value.update.return_value = expected_count
        
        result = self.repository.revoke_all_user_sessions(user_id)
        
        assert result == expected_count
        self.mock_session.query.assert_called_once_with(UserSessionModel)
        query_mock.filter.assert_called_once()
        query_mock.filter.return_value.update.assert_called_once()
        self.mock_session.commit.assert_called_once()

    def test_delete_expired_sessions(self):
        """Test deleting expired sessions."""
        expected_count = 10
        
        # Mock the delete query
        query_mock = self.mock_session.query.return_value
        query_mock.filter.return_value.delete.return_value = expected_count
        
        result = self.repository.delete_expired_sessions()
        
        assert result == expected_count
        self.mock_session.query.assert_called_once_with(UserSessionModel)
        query_mock.filter.assert_called_once()
        query_mock.filter.return_value.delete.assert_called_once()
        self.mock_session.commit.assert_called_once()

    def test_count_user_sessions(self):
        """Test counting all sessions for a user."""
        user_id = uuid4()
        expected_count = 7
        
        query_mock = self.mock_session.query.return_value
        query_mock.filter.return_value.count.return_value = expected_count
        
        result = self.repository.count_user_sessions(user_id)
        
        assert result == expected_count
        self.mock_session.query.assert_called_once_with(UserSessionModel)
        query_mock.filter.assert_called_once()
        query_mock.filter.return_value.count.assert_called_once()

    def test_count_active_user_sessions(self):
        """Test counting active sessions for a user."""
        user_id = uuid4()
        expected_count = 3
        
        query_mock = self.mock_session.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.filter.return_value.count.return_value = expected_count
        
        result = self.repository.count_active_user_sessions(user_id)
        
        assert result == expected_count
        self.mock_session.query.assert_called_once_with(UserSessionModel)
        # Should have two filters: user_id and status
        assert query_mock.filter.call_count == 1
        assert filter_mock.filter.call_count == 1

    def test_model_to_entity_conversion(self):
        """Test conversion from SQLAlchemy model to domain entity."""
        session_id = uuid4()
        user_id = uuid4()
        
        mock_session_model = Mock(spec=UserSessionModel)
        mock_session_model.id = session_id
        mock_session_model.user_id = user_id
        mock_session_model.session_token = "test_token_123"
        mock_session_model.status = SessionStatus.ACTIVE.value
        mock_session_model.login_at = datetime.utcnow()
        mock_session_model.logout_at = None
        mock_session_model.expires_at = datetime.utcnow() + timedelta(hours=24)
        mock_session_model.metadata = {"browser": "Chrome"}
        mock_session_model.ip_address = "192.168.1.1"
        mock_session_model.user_agent = "Mozilla/5.0"
        mock_session_model.created_at = datetime.utcnow()
        mock_session_model.updated_at = None
        
        entity = self.repository._model_to_entity(mock_session_model)
        
        assert isinstance(entity, UserSession)
        assert entity.id == session_id
        assert entity.user_id == user_id
        assert entity.session_token == "test_token_123"
        assert entity.status == SessionStatus.ACTIVE
        assert entity.metadata == {"browser": "Chrome"}
        assert entity.ip_address == "192.168.1.1"
        assert entity.user_agent == "Mozilla/5.0"

    def test_entity_to_model_conversion(self):
        """Test conversion from domain entity to SQLAlchemy model."""
        user_id = uuid4()
        session = UserSession.create(
            user_id=user_id,
            session_token="test_token_123",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            metadata={"browser": "Chrome"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        model = self.repository._entity_to_model(session)
        
        assert isinstance(model, UserSessionModel)
        assert model.id == session.id
        assert model.user_id == session.user_id
        assert model.session_token == session.session_token
        assert model.status == session.status.value
        assert model.login_at == session.login_at
        assert model.logout_at == session.logout_at
        assert model.expires_at == session.expires_at
        assert model.metadata == session.metadata
        assert model.ip_address == session.ip_address
        assert model.user_agent == session.user_agent
        assert model.created_at == session.created_at
        assert model.updated_at == session.updated_at

    def test_delete_session(self):
        """Test deleting a session."""
        session_id = uuid4()
        
        # Mock session model
        mock_session_model = Mock(spec=UserSessionModel)
        mock_session_model.id = session_id
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_session_model
        
        result = self.repository.delete(session_id)
        
        assert result is True
        self.mock_session.delete.assert_called_once_with(mock_session_model)
        self.mock_session.commit.assert_called_once()

    def test_delete_session_not_found(self):
        """Test deleting session when session doesn't exist."""
        session_id = uuid4()
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = self.repository.delete(session_id)
        
        assert result is False
        self.mock_session.delete.assert_not_called()
        self.mock_session.commit.assert_not_called()

    def test_session_rollback_on_error(self):
        """Test that session is rolled back on errors."""
        user_id = uuid4()
        session = UserSession.create(
            user_id=user_id,
            session_token="test_token_123",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        # Mock an error during commit
        self.mock_session.merge.return_value = Mock()
        self.mock_session.commit.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            self.repository.save(session)
        
        self.mock_session.rollback.assert_called_once()

    def test_get_active_sessions_filter(self):
        """Test that active sessions are properly filtered."""
        user_id = uuid4()
        
        # Create mix of active and inactive sessions
        sessions = []
        for i, status in enumerate([SessionStatus.ACTIVE, SessionStatus.EXPIRED, SessionStatus.LOGGED_OUT]):
            mock_session = Mock(spec=UserSessionModel)
            mock_session.id = uuid4()
            mock_session.user_id = user_id
            mock_session.session_token = f"token_{i}"
            mock_session.status = status.value
            mock_session.login_at = datetime.utcnow()
            mock_session.logout_at = None if status == SessionStatus.ACTIVE else datetime.utcnow()
            mock_session.expires_at = datetime.utcnow() + timedelta(hours=24)
            mock_session.metadata = None
            mock_session.ip_address = None
            mock_session.user_agent = None
            mock_session.created_at = datetime.utcnow()
            mock_session.updated_at = None
            sessions.append(mock_session)
        
        # Mock only active session being returned
        query_mock = self.mock_session.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.filter.return_value.order_by.return_value.all.return_value = [sessions[0]]  # Only active
        
        result = self.repository.get_active_user_sessions(user_id)
        
        assert len(result) == 1
        assert result[0].status == SessionStatus.ACTIVE

    def test_repository_initialization(self):
        """Test repository initialization with session."""
        session = Mock(spec=Session)
        repo = SqlAlchemyUserSessionRepository(session)
        
        assert repo._session == session

    def test_metadata_handling(self):
        """Test proper handling of session metadata."""
        user_id = uuid4()
        metadata = {"browser": "Chrome", "version": "91.0", "device": "desktop"}
        
        session = UserSession.create(
            user_id=user_id,
            session_token="test_token_123",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            metadata=metadata
        )
        
        # Test entity to model conversion
        model = self.repository._entity_to_model(session)
        assert model.metadata == metadata
        
        # Test model to entity conversion
        mock_model = Mock(spec=UserSessionModel)
        mock_model.id = session.id
        mock_model.user_id = user_id
        mock_model.session_token = "test_token_123"
        mock_model.status = SessionStatus.ACTIVE.value
        mock_model.login_at = session.login_at
        mock_model.logout_at = None
        mock_model.expires_at = session.expires_at
        mock_model.metadata = metadata
        mock_model.ip_address = None
        mock_model.user_agent = None
        mock_model.created_at = session.created_at
        mock_model.updated_at = None
        
        entity = self.repository._model_to_entity(mock_model)
        assert entity.metadata == metadata