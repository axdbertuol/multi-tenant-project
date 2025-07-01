import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from user.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from user.infrastructure.database.models import UserModel
from user.domain.entities.user import User
from user.domain.value_objects.email import Email


class TestSqlAlchemyUserRepository:
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.repository = SqlAlchemyUserRepository(self.mock_session)

    def test_save_new_user(self):
        """Test saving a new user."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        
        # Mock session behavior
        self.mock_session.merge.return_value = Mock()
        self.mock_session.commit.return_value = None
        
        result = self.repository.save(user)
        
        assert result == user
        self.mock_session.merge.assert_called_once()
        self.mock_session.commit.assert_called_once()
        
        # Verify the model was created correctly
        merge_call_args = self.mock_session.merge.call_args[0][0]
        assert isinstance(merge_call_args, UserModel)
        assert merge_call_args.email == user.email.value

    def test_save_existing_user(self):
        """Test saving an existing user (update)."""
        user_id = uuid4()
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        user = user.model_copy(update={"id": user_id})
        
        # Mock session behavior
        self.mock_session.merge.return_value = Mock()
        self.mock_session.commit.return_value = None
        
        result = self.repository.save(user)
        
        assert result == user
        self.mock_session.merge.assert_called_once()
        self.mock_session.commit.assert_called_once()

    def test_save_integrity_error(self):
        """Test saving user with integrity constraint violation."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        
        # Mock integrity error (e.g., duplicate email)
        self.mock_session.merge.side_effect = IntegrityError("", "", "")
        
        with pytest.raises(ValueError, match="User with this email already exists"):
            self.repository.save(user)
        
        self.mock_session.rollback.assert_called_once()

    def test_get_by_id_found(self):
        """Test getting user by ID when user exists."""
        user_id = uuid4()
        
        # Mock database model
        mock_user_model = Mock(spec=UserModel)
        mock_user_model.id = user_id
        mock_user_model.email = "test@example.com"
        mock_user_model.name = "Test User"
        mock_user_model.password_hash = "hashed_password"
        mock_user_model.is_active = True
        mock_user_model.is_verified = True
        mock_user_model.created_at = Mock()
        mock_user_model.updated_at = None
        mock_user_model.last_login_at = None
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_user_model
        
        result = self.repository.get_by_id(user_id)
        
        assert isinstance(result, User)
        assert result.id == user_id
        assert result.email.value == "test@example.com"
        assert result.name == "Test User"
        
        self.mock_session.query.assert_called_once_with(UserModel)

    def test_get_by_id_not_found(self):
        """Test getting user by ID when user doesn't exist."""
        user_id = uuid4()
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = self.repository.get_by_id(user_id)
        
        assert result is None

    def test_get_by_email_found(self):
        """Test getting user by email when user exists."""
        email = Email(value="test@example.com")
        
        # Mock database model
        mock_user_model = Mock(spec=UserModel)
        mock_user_model.id = uuid4()
        mock_user_model.email = email.value
        mock_user_model.name = "Test User"
        mock_user_model.password_hash = "hashed_password"
        mock_user_model.is_active = True
        mock_user_model.is_verified = True
        mock_user_model.created_at = Mock()
        mock_user_model.updated_at = None
        mock_user_model.last_login_at = None
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_user_model
        
        result = self.repository.get_by_email(email)
        
        assert isinstance(result, User)
        assert result.email.value == email.value
        
        self.mock_session.query.assert_called_once_with(UserModel)

    def test_get_by_email_not_found(self):
        """Test getting user by email when user doesn't exist."""
        email = Email(value="nonexistent@example.com")
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = self.repository.get_by_email(email)
        
        assert result is None

    def test_delete_user_found(self):
        """Test deleting user when user exists."""
        user_id = uuid4()
        
        # Mock user model
        mock_user_model = Mock(spec=UserModel)
        mock_user_model.id = user_id
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_user_model
        
        result = self.repository.delete(user_id)
        
        assert result is True
        self.mock_session.delete.assert_called_once_with(mock_user_model)
        self.mock_session.commit.assert_called_once()

    def test_delete_user_not_found(self):
        """Test deleting user when user doesn't exist."""
        user_id = uuid4()
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = self.repository.delete(user_id)
        
        assert result is False
        self.mock_session.delete.assert_not_called()
        self.mock_session.commit.assert_not_called()

    def test_list_active_users(self):
        """Test listing active users with pagination."""
        limit = 10
        offset = 0
        
        # Mock user models
        mock_users = []
        for i in range(3):
            mock_user = Mock(spec=UserModel)
            mock_user.id = uuid4()
            mock_user.email = f"user{i}@example.com"
            mock_user.name = f"User {i}"
            mock_user.password_hash = "hashed_password"
            mock_user.is_active = True
            mock_user.is_verified = True
            mock_user.created_at = Mock()
            mock_user.updated_at = None
            mock_user.last_login_at = None
            mock_users.append(mock_user)
        
        query_mock = self.mock_session.query.return_value
        query_mock.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_users
        
        result = self.repository.list_active_users(limit=limit, offset=offset)
        
        assert len(result) == 3
        for i, user in enumerate(result):
            assert isinstance(user, User)
            assert user.email.value == f"user{i}@example.com"
        
        # Verify query construction
        self.mock_session.query.assert_called_once_with(UserModel)
        query_mock.filter.assert_called_once()
        query_mock.filter.return_value.order_by.assert_called_once()
        query_mock.filter.return_value.order_by.return_value.offset.assert_called_once_with(offset)
        query_mock.filter.return_value.order_by.return_value.offset.return_value.limit.assert_called_once_with(limit)

    def test_count_active_users(self):
        """Test counting active users."""
        expected_count = 42
        
        query_mock = self.mock_session.query.return_value
        query_mock.filter.return_value.count.return_value = expected_count
        
        result = self.repository.count_active_users()
        
        assert result == expected_count
        self.mock_session.query.assert_called_once_with(UserModel)
        query_mock.filter.assert_called_once()
        query_mock.filter.return_value.count.assert_called_once()

    def test_model_to_entity_conversion(self):
        """Test conversion from SQLAlchemy model to domain entity."""
        user_id = uuid4()
        
        # Create a complete mock user model
        mock_user_model = Mock(spec=UserModel)
        mock_user_model.id = user_id
        mock_user_model.email = "test@example.com"
        mock_user_model.name = "Test User"
        mock_user_model.password_hash = "hashed_password"
        mock_user_model.is_active = True
        mock_user_model.is_verified = True
        mock_user_model.created_at = Mock()
        mock_user_model.updated_at = Mock()
        mock_user_model.last_login_at = Mock()
        
        # Test the conversion
        entity = self.repository._model_to_entity(mock_user_model)
        
        assert isinstance(entity, User)
        assert entity.id == user_id
        assert entity.email.value == "test@example.com"
        assert entity.name == "Test User"
        assert entity.is_active is True
        assert entity.is_verified is True

    def test_entity_to_model_conversion(self):
        """Test conversion from domain entity to SQLAlchemy model."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        
        model = self.repository._entity_to_model(user)
        
        assert isinstance(model, UserModel)
        assert model.id == user.id
        assert model.email == user.email.value
        assert model.name == user.name
        assert model.password_hash == user.password.hashed_value
        assert model.is_active == user.is_active
        assert model.is_verified == user.is_verified
        assert model.created_at == user.created_at
        assert model.updated_at == user.updated_at
        assert model.last_login_at == user.last_login_at

    def test_exists_by_email(self):
        """Test checking if user exists by email."""
        email = Email(value="test@example.com")
        
        # Test when user exists
        query_mock = self.mock_session.query.return_value
        query_mock.filter.return_value.first.return_value = Mock()
        
        result = self.repository.exists_by_email(email)
        assert result is True
        
        # Test when user doesn't exist
        query_mock.filter.return_value.first.return_value = None
        
        result = self.repository.exists_by_email(email)
        assert result is False

    def test_session_rollback_on_error(self):
        """Test that session is rolled back on errors."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        
        # Mock an error during commit
        self.mock_session.merge.return_value = Mock()
        self.mock_session.commit.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            self.repository.save(user)
        
        self.mock_session.rollback.assert_called_once()

    def test_get_user_organizations(self):
        """Test getting organizations for a user."""
        user_id = uuid4()
        
        # This method should delegate to organization repository
        # For now, we'll test that it returns empty list
        result = self.repository.get_user_organizations(user_id)
        
        assert result == []

    def test_repository_initialization(self):
        """Test repository initialization with session."""
        session = Mock(spec=Session)
        repo = SqlAlchemyUserRepository(session)
        
        assert repo._session == session