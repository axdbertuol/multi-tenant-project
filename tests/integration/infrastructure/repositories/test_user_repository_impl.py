import pytest
from uuid import uuid4
from src.domain.entities.user import User
from src.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from tests.factories.user_factory import UserFactory


@pytest.mark.integration
class TestUserRepositoryImpl:
    """Integration tests for UserRepositoryImpl."""
    
    @pytest.fixture
    def user_repository(self, db_session):
        """Create UserRepositoryImpl instance with test database session."""
        return UserRepositoryImpl(db_session)
    
    @pytest.mark.io
     def test_create_user(self, user_repository):
        """Test creating a user in the database."""
        # Arrange
        user = UserFactory.create_user(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        # Act
        created_user =  user_repository.create(user)
        
        # Assert
        assert created_user.id == user.id
        assert created_user.email.value == "test@example.com"
        assert created_user.name == "Test User"
        assert created_user.password.verify("password123")
        assert created_user.is_active is True
    
    @pytest.mark.io
     def test_get_by_id_existing_user(self, user_repository):
        """Test getting an existing user by ID."""
        # Arrange
        user = UserFactory.create_user()
        created_user =  user_repository.create(user)
        
        # Act
        retrieved_user =  user_repository.get_by_id(created_user.id)
        
        # Assert
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email.value == created_user.email.value
        assert retrieved_user.name == created_user.name
    
    @pytest.mark.io
     def test_get_by_id_non_existent_user(self, user_repository):
        """Test getting a non-existent user by ID."""
        # Arrange
        non_existent_id = uuid4()
        
        # Act
        result =  user_repository.get_by_id(non_existent_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.io
     def test_get_by_email_existing_user(self, user_repository):
        """Test getting an existing user by email."""
        # Arrange
        user = UserFactory.create_user(email="test@example.com")
         user_repository.create(user)
        
        # Act
        retrieved_user =  user_repository.get_by_email("test@example.com")
        
        # Assert
        assert retrieved_user is not None
        assert retrieved_user.email.value == "test@example.com"
        assert retrieved_user.id == user.id
    
    @pytest.mark.io
     def test_get_by_email_non_existent_user(self, user_repository):
        """Test getting a non-existent user by email."""
        # Act
        result =  user_repository.get_by_email("nonexistent@example.com")
        
        # Assert
        assert result is None
    
    @pytest.mark.io
     def test_get_all_users(self, user_repository):
        """Test getting all users."""
        # Arrange
        users = [
            UserFactory.create_user(email="user1@example.com"),
            UserFactory.create_user(email="user2@example.com"),
            UserFactory.create_user(email="user3@example.com")
        ]
        
        for user in users:
             user_repository.create(user)
        
        # Act
        all_users =  user_repository.get_all()
        
        # Assert
        assert len(all_users) == 3
        emails = [user.email.value for user in all_users]
        assert "user1@example.com" in emails
        assert "user2@example.com" in emails
        assert "user3@example.com" in emails
    
    @pytest.mark.io
     def test_update_user(self, user_repository):
        """Test updating a user."""
        # Arrange
        user = UserFactory.create_user(name="Original Name")
        created_user =  user_repository.create(user)
        
        # Update the user
        updated_user = created_user.update_name("Updated Name")
        
        # Act
        result =  user_repository.update(updated_user)
        
        # Assert
        assert result.name == "Updated Name"
        assert result.updated_at is not None
        assert result.id == created_user.id
        
        # Verify in database
        retrieved_user =  user_repository.get_by_id(created_user.id)
        assert retrieved_user.name == "Updated Name"
    
    @pytest.mark.io
     def test_update_user_password(self, user_repository):
        """Test updating a user's password."""
        # Arrange
        user = UserFactory.create_user(password="oldpassword123")
        created_user =  user_repository.create(user)
        
        # Update password
        updated_user = created_user.change_password("newpassword456")
        
        # Act
        result =  user_repository.update(updated_user)
        
        # Assert
        assert result.password.verify("newpassword456")
        assert not result.password.verify("oldpassword123")
        
        # Verify in database
        retrieved_user =  user_repository.get_by_id(created_user.id)
        assert retrieved_user.password.verify("newpassword456")
    
    @pytest.mark.io
     def test_update_user_activation_status(self, user_repository):
        """Test updating user activation status."""
        # Arrange
        user = UserFactory.create_user()
        created_user =  user_repository.create(user)
        
        # Deactivate user
        deactivated_user = created_user.deactivate()
        
        # Act
        result =  user_repository.update(deactivated_user)
        
        # Assert
        assert result.is_active is False
        assert result.updated_at is not None
        
        # Verify in database
        retrieved_user =  user_repository.get_by_id(created_user.id)
        assert retrieved_user.is_active is False
    
    @pytest.mark.io
     def test_delete_user(self, user_repository):
        """Test deleting a user."""
        # Arrange
        user = UserFactory.create_user()
        created_user =  user_repository.create(user)
        
        # Act
        result =  user_repository.delete(created_user.id)
        
        # Assert
        assert result is True
        
        # Verify user is deleted
        deleted_user =  user_repository.get_by_id(created_user.id)
        assert deleted_user is None
    
    @pytest.mark.io
     def test_delete_non_existent_user(self, user_repository):
        """Test deleting a non-existent user."""
        # Arrange
        non_existent_id = uuid4()
        
        # Act
        result =  user_repository.delete(non_existent_id)
        
        # Assert
        assert result is False
    
    @pytest.mark.io
     def test_email_uniqueness_constraint(self, user_repository):
        """Test that email uniqueness is enforced at database level."""
        # Arrange
        user1 = UserFactory.create_user(email="duplicate@example.com")
        user2 = UserFactory.create_user(email="duplicate@example.com")
        
        # Act
         user_repository.create(user1)
        
        # Assert - Second user with same email should fail
        with pytest.raises(Exception):  # Database integrity error
             user_repository.create(user2)
    
    @pytest.mark.io
     def test_password_hashing_persistence(self, user_repository):
        """Test that passwords are properly hashed and persisted."""
        # Arrange
        plain_password = "mysecretpassword123"
        user = UserFactory.create_user(password=plain_password)
        
        # Act
        created_user =  user_repository.create(user)
        retrieved_user =  user_repository.get_by_id(created_user.id)
        
        # Assert
        assert retrieved_user.password.verify(plain_password)
        assert retrieved_user.password.hashed_value != plain_password
        assert len(retrieved_user.password.hashed_value) > len(plain_password)
    
    @pytest.mark.io
     def test_user_timestamps(self, user_repository):
        """Test that user timestamps are properly handled."""
        # Arrange
        user = UserFactory.create_user()
        
        # Act
        created_user =  user_repository.create(user)
        
        # Assert
        assert created_user.created_at is not None
        assert created_user.updated_at is None
        
        # Update user and check updated_at
        updated_user = created_user.update_name("New Name")
        result =  user_repository.update(updated_user)
        
        assert result.updated_at is not None
        assert result.updated_at > result.created_at
    
    @pytest.mark.io
     def test_domain_model_mapping(self, user_repository):
        """Test that domain entities are properly mapped to/from database models."""
        # Arrange
        user = UserFactory.create_user(
            email="mapping@example.com",
            name="Mapping Test",
            password="password123"
        )
        
        # Act - Create and retrieve
        created_user =  user_repository.create(user)
        retrieved_user =  user_repository.get_by_id(created_user.id)
        
        # Assert - All domain properties preserved
        assert isinstance(retrieved_user, User)
        assert retrieved_user.id == user.id
        assert retrieved_user.email.value == "mapping@example.com"
        assert retrieved_user.name == "Mapping Test"
        assert retrieved_user.password.verify("password123")
        assert retrieved_user.is_active == user.is_active
        assert retrieved_user.created_at == created_user.created_at