import pytest
from datetime import datetime
from uuid import UUID
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password


class TestUser:
    """Unit tests for User domain entity."""
    
    def test_create_user(self):
        """Test creating a new user."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        assert isinstance(user.id, UUID)
        assert isinstance(user.email, Email)
        assert user.email.value == "test@example.com"
        assert user.name == "Test User"
        assert isinstance(user.password, Password)
        assert user.password.verify("password123")
        assert isinstance(user.created_at, datetime)
        assert user.updated_at is None
        assert user.is_active is True
    
    def test_user_immutability(self):
        """Test that user entity is immutable."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        # Should not be able to directly modify attributes
        with pytest.raises(AttributeError):
            user.name = "New Name"
        
        with pytest.raises(AttributeError):
            user.email = Email(value="new@example.com")
    
    def test_update_name(self):
        """Test updating user name."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        updated_user = user.update_name("Updated Name")
        
        # Original user unchanged
        assert user.name == "Test User"
        assert user.updated_at is None
        
        # New user object with changes
        assert updated_user.name == "Updated Name"
        assert updated_user.updated_at is not None
        assert updated_user.id == user.id
        assert updated_user.email == user.email
        assert updated_user.password == user.password
    
    def test_deactivate_user(self):
        """Test deactivating a user."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        deactivated_user = user.deactivate()
        
        # Original user unchanged
        assert user.is_active is True
        assert user.updated_at is None
        
        # New user object with changes
        assert deactivated_user.is_active is False
        assert deactivated_user.updated_at is not None
        assert deactivated_user.id == user.id
    
    def test_activate_user(self):
        """Test activating a user."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        # First deactivate
        deactivated_user = user.deactivate()
        
        # Then activate
        activated_user = deactivated_user.activate()
        
        assert activated_user.is_active is True
        assert activated_user.updated_at is not None
        assert activated_user.id == user.id
    
    def test_change_password(self):
        """Test changing user password."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        updated_user = user.change_password("newpassword123")
        
        # Original user unchanged
        assert user.password.verify("password123")
        assert user.updated_at is None
        
        # New user object with changes
        assert updated_user.password.verify("newpassword123")
        assert not updated_user.password.verify("password123")
        assert updated_user.updated_at is not None
        assert updated_user.id == user.id
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        assert user.verify_password("password123") is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        assert user.verify_password("wrongpassword") is False
    
    def test_user_with_invalid_email(self):
        """Test creating user with invalid email."""
        with pytest.raises(ValueError, match="Invalid email format"):
            User.create(
                email="invalid-email",
                name="Test User",
                password="password123"
            )
    
    def test_user_with_invalid_password(self):
        """Test creating user with invalid password."""
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            User.create(
                email="test@example.com",
                name="Test User",
                password="short"
            )
    
    def test_user_with_empty_name(self):
        """Test creating user with empty name."""
        # This should work as name validation is handled at DTO level
        user = User.create(
            email="test@example.com",
            name="",
            password="password123"
        )
        
        assert user.name == ""
    
    def test_user_creation_timestamps(self):
        """Test user creation timestamps."""
        before_creation = datetime.utcnow()
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        after_creation = datetime.utcnow()
        
        assert before_creation <= user.created_at <= after_creation
        assert user.updated_at is None
    
    def test_user_update_timestamps(self):
        """Test user update timestamps."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        # Wait a bit to ensure different timestamp
        import time
        time.sleep(0.001)
        
        before_update = datetime.utcnow()
        updated_user = user.update_name("New Name")
        after_update = datetime.utcnow()
        
        assert before_update <= updated_user.updated_at <= after_update
        assert updated_user.created_at == user.created_at
    
    def test_user_equality(self):
        """Test user equality based on ID."""
        user1 = User.create(
            email="test1@example.com",
            name="User 1",
            password="password123"
        )
        
        user2 = User.create(
            email="test2@example.com",
            name="User 2",
            password="password456"
        )
        
        # Different users should not be equal
        assert user1 != user2
        
        # Same user with modifications should still be equal (same ID)
        updated_user1 = user1.update_name("Updated Name")
        assert user1.id == updated_user1.id
    
    def test_user_string_representation(self):
        """Test user string representation."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        # Should not expose sensitive information
        user_str = str(user)
        assert "password" not in user_str.lower()
        assert "test@example.com" in user_str or "Test User" in user_str