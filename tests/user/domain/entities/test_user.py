import pytest
from datetime import datetime
from uuid import UUID

from user.domain.entities.user import User
from user.domain.value_objects.email import Email
from user.domain.value_objects.password import Password


class TestUser:
    def test_create_user(self):
        """Test creating a new user."""
        email = "test@example.com"
        name = "Test User"
        password = "securepassword123"
        
        user = User.create(email=email, name=name, password=password)
        
        assert isinstance(user.id, UUID)
        assert user.email.value == email
        assert user.name == name
        assert isinstance(user.password, Password)
        assert user.is_active is True
        assert user.is_verified is True
        assert isinstance(user.created_at, datetime)
        assert user.updated_at is None
        assert user.last_login_at is None

    def test_verify_password(self):
        """Test password verification."""
        password = "securepassword123"
        user = User.create(
            email="test@example.com",
            name="Test User",
            password=password
        )
        
        assert user.verify_password(password) is True
        assert user.verify_password("wrongpassword") is False

    def test_update_name(self):
        """Test updating user name."""
        user = User.create(
            email="test@example.com",
            name="Old Name",
            password="password123"
        )
        
        new_name = "New Name"
        updated_user = user.update_name(new_name)
        
        assert updated_user.name == new_name
        assert updated_user.updated_at is not None
        assert updated_user.id == user.id
        assert updated_user.email == user.email

    def test_deactivate_user(self):
        """Test deactivating a user."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        deactivated_user = user.deactivate()
        
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
        deactivated_user = user.deactivate()
        
        activated_user = deactivated_user.activate()
        
        assert activated_user.is_active is True
        assert activated_user.updated_at is not None
        assert activated_user.id == user.id

    def test_change_password(self):
        """Test changing user password."""
        old_password = "oldpassword123"
        new_password = "newpassword456"
        
        user = User.create(
            email="test@example.com",
            name="Test User",
            password=old_password
        )
        
        updated_user = user.change_password(new_password)
        
        assert updated_user.verify_password(new_password) is True
        assert updated_user.verify_password(old_password) is False
        assert updated_user.updated_at is not None
        assert updated_user.id == user.id

    def test_update_last_login(self):
        """Test updating last login timestamp."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        login_time = datetime.utcnow()
        updated_user = user.update_last_login(login_time)
        
        assert updated_user.last_login_at == login_time
        assert updated_user.updated_at is not None
        assert updated_user.id == user.id

    def test_can_access_organization(self):
        """Test organization access rules."""
        from uuid import uuid4
        
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        organization_id = uuid4()
        
        # Active user can access
        assert user.can_access_organization(organization_id) is True
        
        # Inactive user cannot access
        inactive_user = user.deactivate()
        assert inactive_user.can_access_organization(organization_id) is False

    def test_user_immutability(self):
        """Test that user operations return new instances."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        updated_user = user.update_name("New Name")
        
        # Original user should be unchanged
        assert user.name == "Test User"
        assert user.updated_at is None
        
        # Updated user should have changes
        assert updated_user.name == "New Name"
        assert updated_user.updated_at is not None
        
        # Should be different instances
        assert user is not updated_user

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
        
        # Same user with updated name should be equal
        updated_user1 = user1.update_name("Updated Name")
        
        assert user1.id == updated_user1.id
        assert user1.id != user2.id