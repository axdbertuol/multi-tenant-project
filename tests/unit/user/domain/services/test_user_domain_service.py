import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from user.domain.services.user_domain_service import UserDomainService
from user.domain.entities.user import User
from user.domain.value_objects.email import Email


class TestUserDomainService:
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_uow = Mock()
        self.mock_user_repository = Mock()
        self.mock_uow.get_repository.return_value = self.mock_user_repository
        
        self.service = UserDomainService(self.mock_uow)

    def test_is_email_available_when_no_existing_user(self):
        """Test email availability when no user exists with that email."""
        email = Email(value="test@example.com")
        self.mock_user_repository.get_by_email.return_value = None
        
        result = self.service.is_email_available(email)
        
        assert result is True
        self.mock_user_repository.get_by_email.assert_called_once_with(email)

    def test_is_email_available_when_existing_user_found(self):
        """Test email availability when user exists with that email."""
        email = Email(value="test@example.com")
        existing_user = User.create(
            email="test@example.com",
            name="Existing User",
            password="Password123"
        )
        self.mock_user_repository.get_by_email.return_value = existing_user
        
        result = self.service.is_email_available(email)
        
        assert result is False
        self.mock_user_repository.get_by_email.assert_called_once_with(email)

    def test_is_email_available_excluding_same_user(self):
        """Test email availability when excluding the same user (for updates)."""
        email = Email(value="test@example.com")
        user_id = uuid4()
        existing_user = User.create(
            email="test@example.com",
            name="Existing User",
            password="Password123"
        )
        existing_user = existing_user.model_copy(update={"id": user_id})
        self.mock_user_repository.get_by_email.return_value = existing_user
        
        result = self.service.is_email_available(email, excluding_user_id=user_id)
        
        assert result is True
        self.mock_user_repository.get_by_email.assert_called_once_with(email)

    def test_is_email_available_excluding_different_user(self):
        """Test email availability when excluding different user."""
        email = Email(value="test@example.com")
        existing_user_id = uuid4()
        excluding_user_id = uuid4()
        existing_user = User.create(
            email="test@example.com",
            name="Existing User",
            password="Password123"
        )
        existing_user = existing_user.model_copy(update={"id": existing_user_id})
        self.mock_user_repository.get_by_email.return_value = existing_user
        
        result = self.service.is_email_available(email, excluding_user_id=excluding_user_id)
        
        assert result is False
        self.mock_user_repository.get_by_email.assert_called_once_with(email)

    def test_can_user_be_deleted_user_not_found(self):
        """Test user deletion validation when user not found."""
        user_id = uuid4()
        self.mock_user_repository.get_by_id.return_value = None
        
        can_delete, reason = self.service.can_user_be_deleted(user_id)
        
        assert can_delete is False
        assert reason == "User not found"
        self.mock_user_repository.get_by_id.assert_called_once_with(user_id)

    def test_can_user_be_deleted_user_exists(self):
        """Test user deletion validation when user exists."""
        user_id = uuid4()
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="Password123"
        )
        self.mock_user_repository.get_by_id.return_value = user
        
        can_delete, reason = self.service.can_user_be_deleted(user_id)
        
        assert can_delete is True
        assert reason == "Can be deleted"
        self.mock_user_repository.get_by_id.assert_called_once_with(user_id)

    def test_validate_user_activation_already_active(self):
        """Test user activation validation when user is already active."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="Password123"
        )
        # User is active by default
        
        can_activate, reason = self.service.validate_user_activation(user)
        
        assert can_activate is False
        assert reason == "User is already active"

    def test_validate_user_activation_inactive_user(self):
        """Test user activation validation when user is inactive."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="Password123"
        )
        inactive_user = user.deactivate()
        
        can_activate, reason = self.service.validate_user_activation(inactive_user)
        
        assert can_activate is True
        assert reason == "Can be activated"

    def test_validate_user_deactivation_already_inactive(self):
        """Test user deactivation validation when user is already inactive."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="Password123"
        )
        inactive_user = user.deactivate()
        
        can_deactivate, reason = self.service.validate_user_deactivation(inactive_user)
        
        assert can_deactivate is False
        assert reason == "User is already inactive"

    def test_validate_user_deactivation_active_user(self):
        """Test user deactivation validation when user is active."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="Password123"
        )
        
        can_deactivate, reason = self.service.validate_user_deactivation(user)
        
        assert can_deactivate is True
        assert reason == "Can be deactivated"

    def test_service_uses_correct_repository(self):
        """Test that service uses the correct repository from UnitOfWork."""
        # Verify the service gets the user repository from UnitOfWork
        self.mock_uow.get_repository.assert_called_once_with("user")
        assert self.service._user_repository == self.mock_user_repository

    def test_email_validation_edge_cases(self):
        """Test email availability with various email formats."""
        test_cases = [
            "user@example.com",
            "user+tag@example.com",
            "user.name@sub.example.com",
            "USER@EXAMPLE.COM"  # Should be normalized to lowercase
        ]
        
        for email_str in test_cases:
            email = Email(value=email_str)
            self.mock_user_repository.get_by_email.return_value = None
            
            result = self.service.is_email_available(email)
            
            assert result is True

    def test_concurrent_email_check_scenarios(self):
        """Test email availability in concurrent scenarios."""
        email = Email(value="test@example.com")
        user1_id = uuid4()
        user2_id = uuid4()
        
        # Scenario 1: User1 wants to update to email that User2 has
        existing_user2 = User.create(
            email="test@example.com",
            name="User 2",
            password="Password123"
        )
        existing_user2 = existing_user2.model_copy(update={"id": user2_id})
        self.mock_user_repository.get_by_email.return_value = existing_user2
        
        result = self.service.is_email_available(email, excluding_user_id=user1_id)
        
        assert result is False  # Can't use email that belongs to another user