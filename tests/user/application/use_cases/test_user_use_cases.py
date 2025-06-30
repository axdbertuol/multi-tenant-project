import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from user.application.use_cases.user_use_cases import UserUseCase
from user.application.dtos.user_dto import (
    UserCreateDTO,
    UserUpdateDTO,
    UserChangePasswordDTO,
    UserResponseDTO
)
from user.domain.entities.user import User
from user.domain.value_objects.email import Email


class TestUserUseCase:
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_uow = Mock()
        self.mock_user_repository = Mock()
        self.mock_user_domain_service = Mock()
        
        self.mock_uow.get_repository.return_value = self.mock_user_repository
        self.mock_uow.__enter__ = Mock(return_value=self.mock_uow)
        self.mock_uow.__exit__ = Mock(return_value=None)
        
        # Patch the domain service creation
        with Mock() as mock_service_class:
            mock_service_class.return_value = self.mock_user_domain_service
            self.use_case = UserUseCase(self.mock_uow)
            self.use_case._user_domain_service = self.mock_user_domain_service

    def test_create_user_successful(self):
        """Test successful user creation."""
        dto = UserCreateDTO(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        
        # Mock domain service
        self.mock_user_domain_service.is_email_available.return_value = True
        
        # Mock repository save
        created_user = User.create(
            email=dto.email,
            name=dto.name,
            password=dto.password
        )
        self.mock_user_repository.save.return_value = created_user
        
        result = self.use_case.create_user(dto)
        
        assert isinstance(result, UserResponseDTO)
        assert result.email == dto.email
        assert result.name == dto.name
        assert result.is_active is True
        
        # Verify interactions
        self.mock_user_domain_service.is_email_available.assert_called_once()
        self.mock_user_repository.save.assert_called_once()
        self.mock_uow.__enter__.assert_called_once()

    def test_create_user_email_already_exists(self):
        """Test user creation when email already exists."""
        dto = UserCreateDTO(
            email="existing@example.com",
            name="Test User",
            password="SecurePass123"
        )
        
        # Mock domain service to return email not available
        self.mock_user_domain_service.is_email_available.return_value = False
        
        with pytest.raises(ValueError, match="Email existing@example.com is already in use"):
            self.use_case.create_user(dto)
        
        # Repository save should not be called
        self.mock_user_repository.save.assert_not_called()

    def test_get_user_by_id_found(self):
        """Test getting user by ID when user exists."""
        user_id = uuid4()
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        user = user.model_copy(update={"id": user_id})
        
        self.mock_user_repository.get_by_id.return_value = user
        
        result = self.use_case.get_user_by_id(user_id)
        
        assert isinstance(result, UserResponseDTO)
        assert result.id == user_id
        assert result.email == user.email.value
        
        self.mock_user_repository.get_by_id.assert_called_once_with(user_id)

    def test_get_user_by_id_not_found(self):
        """Test getting user by ID when user doesn't exist."""
        user_id = uuid4()
        
        self.mock_user_repository.get_by_id.return_value = None
        
        result = self.use_case.get_user_by_id(user_id)
        
        assert result is None
        self.mock_user_repository.get_by_id.assert_called_once_with(user_id)

    def test_get_user_by_email_found(self):
        """Test getting user by email when user exists."""
        email = "test@example.com"
        user = User.create(
            email=email,
            name="Test User",
            password="SecurePass123"
        )
        
        self.mock_user_repository.get_by_email.return_value = user
        
        result = self.use_case.get_user_by_email(email)
        
        assert isinstance(result, UserResponseDTO)
        assert result.email == email
        
        # Verify Email value object was created and used
        self.mock_user_repository.get_by_email.assert_called_once()
        call_args = self.mock_user_repository.get_by_email.call_args[0][0]
        assert isinstance(call_args, Email)
        assert call_args.value == email

    def test_get_user_by_email_not_found(self):
        """Test getting user by email when user doesn't exist."""
        email = "nonexistent@example.com"
        
        self.mock_user_repository.get_by_email.return_value = None
        
        result = self.use_case.get_user_by_email(email)
        
        assert result is None

    def test_update_user_successful(self):
        """Test successful user update."""
        user_id = uuid4()
        dto = UserUpdateDTO(name="Updated Name", is_active=True)
        
        original_user = User.create(
            email="test@example.com",
            name="Original Name",
            password="SecurePass123"
        )
        original_user = original_user.model_copy(update={"id": user_id})
        
        updated_user = original_user.update_name(dto.name)
        
        self.mock_user_repository.get_by_id.return_value = original_user
        self.mock_user_repository.save.return_value = updated_user
        self.mock_user_domain_service.validate_user_activation.return_value = (True, "Can be activated")
        
        result = self.use_case.update_user(user_id, dto)
        
        assert isinstance(result, UserResponseDTO)
        assert result.name == dto.name
        
        self.mock_user_repository.get_by_id.assert_called_once_with(user_id)
        self.mock_user_repository.save.assert_called_once()

    def test_update_user_not_found(self):
        """Test updating user when user doesn't exist."""
        user_id = uuid4()
        dto = UserUpdateDTO(name="Updated Name")
        
        self.mock_user_repository.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="User not found"):
            self.use_case.update_user(user_id, dto)

    def test_update_user_activate_validation_fails(self):
        """Test user update when activation validation fails."""
        user_id = uuid4()
        dto = UserUpdateDTO(is_active=True)
        
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        inactive_user = user.deactivate()
        inactive_user = inactive_user.model_copy(update={"id": user_id})
        
        self.mock_user_repository.get_by_id.return_value = inactive_user
        self.mock_user_domain_service.validate_user_activation.return_value = (False, "Cannot activate")
        
        with pytest.raises(ValueError, match="Cannot activate user: Cannot activate"):
            self.use_case.update_user(user_id, dto)

    def test_change_password_successful(self):
        """Test successful password change."""
        user_id = uuid4()
        dto = UserChangePasswordDTO(
            current_password="OldPass123",
            new_password="NewPass456"
        )
        
        user = User.create(
            email="test@example.com",
            name="Test User",
            password=dto.current_password
        )
        user = user.model_copy(update={"id": user_id})
        
        updated_user = user.change_password(dto.new_password)
        
        self.mock_user_repository.get_by_id.return_value = user
        self.mock_user_repository.save.return_value = updated_user
        
        result = self.use_case.change_password(user_id, dto)
        
        assert result is True
        self.mock_user_repository.get_by_id.assert_called_once_with(user_id)
        self.mock_user_repository.save.assert_called_once()

    def test_change_password_user_not_found(self):
        """Test password change when user doesn't exist."""
        user_id = uuid4()
        dto = UserChangePasswordDTO(
            current_password="OldPass123",
            new_password="NewPass456"
        )
        
        self.mock_user_repository.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="User not found"):
            self.use_case.change_password(user_id, dto)

    def test_change_password_incorrect_current_password(self):
        """Test password change with incorrect current password."""
        user_id = uuid4()
        dto = UserChangePasswordDTO(
            current_password="WrongPass123",
            new_password="NewPass456"
        )
        
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="CorrectPass123"
        )
        user = user.model_copy(update={"id": user_id})
        
        self.mock_user_repository.get_by_id.return_value = user
        
        with pytest.raises(ValueError, match="Current password is incorrect"):
            self.use_case.change_password(user_id, dto)

    def test_deactivate_user_successful(self):
        """Test successful user deactivation."""
        user_id = uuid4()
        
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        user = user.model_copy(update={"id": user_id})
        
        deactivated_user = user.deactivate()
        
        self.mock_user_repository.get_by_id.return_value = user
        self.mock_user_repository.save.return_value = deactivated_user
        self.mock_user_domain_service.validate_user_deactivation.return_value = (True, "Can be deactivated")
        
        result = self.use_case.deactivate_user(user_id)
        
        assert isinstance(result, UserResponseDTO)
        assert result.is_active is False
        
        self.mock_user_domain_service.validate_user_deactivation.assert_called_once_with(user)

    def test_deactivate_user_validation_fails(self):
        """Test user deactivation when validation fails."""
        user_id = uuid4()
        
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        user = user.model_copy(update={"id": user_id})
        
        self.mock_user_repository.get_by_id.return_value = user
        self.mock_user_domain_service.validate_user_deactivation.return_value = (False, "Cannot deactivate")
        
        with pytest.raises(ValueError, match="Cannot deactivate user: Cannot deactivate"):
            self.use_case.deactivate_user(user_id)

    def test_activate_user_successful(self):
        """Test successful user activation."""
        user_id = uuid4()
        
        user = User.create(
            email="test@example.com",
            name="Test User",
            password="SecurePass123"
        )
        inactive_user = user.deactivate()
        inactive_user = inactive_user.model_copy(update={"id": user_id})
        
        activated_user = inactive_user.activate()
        
        self.mock_user_repository.get_by_id.return_value = inactive_user
        self.mock_user_repository.save.return_value = activated_user
        self.mock_user_domain_service.validate_user_activation.return_value = (True, "Can be activated")
        
        result = self.use_case.activate_user(user_id)
        
        assert isinstance(result, UserResponseDTO)
        assert result.is_active is True

    def test_delete_user_successful(self):
        """Test successful user deletion."""
        user_id = uuid4()
        
        self.mock_user_domain_service.can_user_be_deleted.return_value = (True, "Can be deleted")
        self.mock_user_repository.delete.return_value = True
        
        result = self.use_case.delete_user(user_id)
        
        assert result is True
        self.mock_user_domain_service.can_user_be_deleted.assert_called_once_with(user_id)
        self.mock_user_repository.delete.assert_called_once_with(user_id)

    def test_delete_user_validation_fails(self):
        """Test user deletion when validation fails."""
        user_id = uuid4()
        
        self.mock_user_domain_service.can_user_be_deleted.return_value = (False, "Cannot delete")
        
        with pytest.raises(ValueError, match="Cannot delete user: Cannot delete"):
            self.use_case.delete_user(user_id)
        
        self.mock_user_repository.delete.assert_not_called()

    def test_list_users(self):
        """Test listing users with pagination."""
        users = [
            User.create(email=f"user{i}@example.com", name=f"User {i}", password="Pass123")
            for i in range(3)
        ]
        
        self.mock_user_repository.list_active_users.return_value = users
        self.mock_user_repository.count_active_users.return_value = 3
        
        result = self.use_case.list_users(page=1, page_size=10)
        
        assert len(result.users) == 3
        assert result.total == 3
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_pages == 1
        
        self.mock_user_repository.list_active_users.assert_called_once_with(limit=10, offset=0)
        self.mock_user_repository.count_active_users.assert_called_once()

    def test_check_email_availability(self):
        """Test checking email availability."""
        email = "test@example.com"
        user_id = uuid4()
        
        self.mock_user_domain_service.is_email_available.return_value = True
        
        result = self.use_case.check_email_availability(email, excluding_user_id=user_id)
        
        assert result is True
        
        # Verify Email value object was created
        call_args = self.mock_user_domain_service.is_email_available.call_args[0]
        assert isinstance(call_args[0], Email)
        assert call_args[0].value == email
        assert call_args[1] == user_id