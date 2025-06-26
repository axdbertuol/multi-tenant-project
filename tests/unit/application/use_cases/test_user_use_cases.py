import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4
from src.application.use_cases.user_use_cases import UserUseCases
from src.application.dtos.user_dto import CreateUserDto, UpdateUserDto, ChangePasswordDto
from tests.factories.user_factory import UserFactory


class TestUserUseCases:
    """Unit tests for UserUseCases."""
    
    @pytest.fixture
    def mock_uow(self):
        """Mock Unit of Work."""
        uow = Mock()
        uow.users = AsyncMock()
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock()
        return uow
    
    @pytest.fixture
    def user_use_cases(self, mock_uow):
        """Create UserUseCases instance with mocked dependencies."""
        return UserUseCases(mock_uow)
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_use_cases, mock_uow):
        """Test successful user creation."""
        # Arrange
        create_dto = CreateUserDto(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        mock_uow.users.get_by_email.return_value = None  # No existing user
        created_user = UserFactory.create_user(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        mock_uow.users.create.return_value = created_user
        
        # Act
        result = await user_use_cases.create_user(create_dto)
        
        # Assert
        assert result.email == "test@example.com"
        assert result.name == "Test User"
        assert result.is_active is True
        
        mock_uow.users.get_by_email.assert_called_once_with("test@example.com")
        mock_uow.users.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_email_already_exists(self, user_use_cases, mock_uow):
        """Test user creation with existing email."""
        # Arrange
        create_dto = CreateUserDto(
            email="existing@example.com",
            name="Test User",
            password="password123"
        )
        
        existing_user = UserFactory.create_user(email="existing@example.com")
        mock_uow.users.get_by_email.return_value = existing_user
        
        # Act & Assert
        with pytest.raises(ValueError, match="User with email existing@example.com already exists"):
            await user_use_cases.create_user(create_dto)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_use_cases, mock_uow):
        """Test getting user by ID successfully."""
        # Arrange
        user_id = uuid4()
        user = UserFactory.create_user()
        mock_uow.users.get_by_id.return_value = user
        
        # Act
        result = await user_use_cases.get_user_by_id(user_id)
        
        # Assert
        assert result is not None
        assert result.id == user.id
        assert result.email == str(user.email.value)
        
        mock_uow.users.get_by_id.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_use_cases, mock_uow):
        """Test getting user by ID when user doesn't exist."""
        # Arrange
        user_id = uuid4()
        mock_uow.users.get_by_id.return_value = None
        
        # Act
        result = await user_use_cases.get_user_by_id(user_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_use_cases, mock_uow):
        """Test getting user by email successfully."""
        # Arrange
        email = "test@example.com"
        user = UserFactory.create_user(email=email)
        mock_uow.users.get_by_email.return_value = user
        
        # Act
        result = await user_use_cases.get_user_by_email(email)
        
        # Assert
        assert result is not None
        assert result.email == email
        
        mock_uow.users.get_by_email.assert_called_once_with(email)
    
    @pytest.mark.asyncio
    async def test_get_all_users(self, user_use_cases, mock_uow):
        """Test getting all users."""
        # Arrange
        users = [
            UserFactory.create_user(email="user1@example.com"),
            UserFactory.create_user(email="user2@example.com"),
            UserFactory.create_user(email="user3@example.com")
        ]
        mock_uow.users.get_all.return_value = users
        
        # Act
        result = await user_use_cases.get_all_users()
        
        # Assert
        assert len(result) == 3
        assert all(user_dto.email in ["user1@example.com", "user2@example.com", "user3@example.com"] 
                  for user_dto in result)
        
        mock_uow.users.get_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_use_cases, mock_uow):
        """Test successful user update."""
        # Arrange
        user_id = uuid4()
        update_dto = UpdateUserDto(name="Updated Name")
        
        existing_user = UserFactory.create_user(name="Original Name")
        updated_user = existing_user.update_name("Updated Name")
        
        mock_uow.users.get_by_id.return_value = existing_user
        mock_uow.users.update.return_value = updated_user
        
        # Act
        result = await user_use_cases.update_user(user_id, update_dto)
        
        # Assert
        assert result is not None
        assert result.name == "Updated Name"
        
        mock_uow.users.get_by_id.assert_called_once_with(user_id)
        mock_uow.users.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_use_cases, mock_uow):
        """Test updating non-existent user."""
        # Arrange
        user_id = uuid4()
        update_dto = UpdateUserDto(name="Updated Name")
        
        mock_uow.users.get_by_id.return_value = None
        
        # Act
        result = await user_use_cases.update_user(user_id, update_dto)
        
        # Assert
        assert result is None
        mock_uow.users.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_user_no_changes(self, user_use_cases, mock_uow):
        """Test updating user with no actual changes."""
        # Arrange
        user_id = uuid4()
        update_dto = UpdateUserDto()  # No changes
        
        existing_user = UserFactory.create_user()
        mock_uow.users.get_by_id.return_value = existing_user
        mock_uow.users.update.return_value = existing_user
        
        # Act
        result = await user_use_cases.update_user(user_id, update_dto)
        
        # Assert
        assert result is not None
        mock_uow.users.update.assert_called_once_with(existing_user)
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_use_cases, mock_uow):
        """Test successful user deletion."""
        # Arrange
        user_id = uuid4()
        mock_uow.users.delete.return_value = True
        
        # Act
        result = await user_use_cases.delete_user(user_id)
        
        # Assert
        assert result is True
        mock_uow.users.delete.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_use_cases, mock_uow):
        """Test deleting non-existent user."""
        # Arrange
        user_id = uuid4()
        mock_uow.users.delete.return_value = False
        
        # Act
        result = await user_use_cases.delete_user(user_id)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_deactivate_user_success(self, user_use_cases, mock_uow):
        """Test successful user deactivation."""
        # Arrange
        user_id = uuid4()
        active_user = UserFactory.create_active_user()
        deactivated_user = active_user.deactivate()
        
        mock_uow.users.get_by_id.return_value = active_user
        mock_uow.users.update.return_value = deactivated_user
        
        # Act
        result = await user_use_cases.deactivate_user(user_id)
        
        # Assert
        assert result is not None
        assert result.is_active is False
        
        mock_uow.users.get_by_id.assert_called_once_with(user_id)
        mock_uow.users.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_activate_user_success(self, user_use_cases, mock_uow):
        """Test successful user activation."""
        # Arrange
        user_id = uuid4()
        inactive_user = UserFactory.create_inactive_user()
        activated_user = inactive_user.activate()
        
        mock_uow.users.get_by_id.return_value = inactive_user
        mock_uow.users.update.return_value = activated_user
        
        # Act
        result = await user_use_cases.activate_user(user_id)
        
        # Assert
        assert result is not None
        assert result.is_active is True
        
        mock_uow.users.get_by_id.assert_called_once_with(user_id)
        mock_uow.users.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, user_use_cases, mock_uow):
        """Test successful password change."""
        # Arrange
        user_id = uuid4()
        change_dto = ChangePasswordDto(
            old_password="password123",
            new_password="newpassword456"
        )
        
        user = UserFactory.create_user(password="password123")
        updated_user = user.change_password("newpassword456")
        
        mock_uow.users.get_by_id.return_value = user
        mock_uow.users.update.return_value = updated_user
        
        # Act
        result = await user_use_cases.change_password(user_id, change_dto)
        
        # Assert
        assert result is not None
        
        mock_uow.users.get_by_id.assert_called_once_with(user_id)
        mock_uow.users.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_password_user_not_found(self, user_use_cases, mock_uow):
        """Test password change for non-existent user."""
        # Arrange
        user_id = uuid4()
        change_dto = ChangePasswordDto(
            old_password="password123",
            new_password="newpassword456"
        )
        
        mock_uow.users.get_by_id.return_value = None
        
        # Act
        result = await user_use_cases.change_password(user_id, change_dto)
        
        # Assert
        assert result is None
        mock_uow.users.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self, user_use_cases, mock_uow):
        """Test password change with wrong old password."""
        # Arrange
        user_id = uuid4()
        change_dto = ChangePasswordDto(
            old_password="wrongpassword",
            new_password="newpassword456"
        )
        
        user = UserFactory.create_user(password="password123")
        mock_uow.users.get_by_id.return_value = user
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid old password"):
            await user_use_cases.change_password(user_id, change_dto)
        
        mock_uow.users.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_verify_user_password_success(self, user_use_cases, mock_uow):
        """Test successful password verification."""
        # Arrange
        email = "test@example.com"
        password = "password123"
        
        user = UserFactory.create_user(email=email, password=password)
        mock_uow.users.get_by_email.return_value = user
        
        # Act
        result = await user_use_cases.verify_user_password(email, password)
        
        # Assert
        assert result is not None
        assert result.email == email
        
        mock_uow.users.get_by_email.assert_called_once_with(email)
    
    @pytest.mark.asyncio
    async def test_verify_user_password_user_not_found(self, user_use_cases, mock_uow):
        """Test password verification for non-existent user."""
        # Arrange
        email = "nonexistent@example.com"
        password = "password123"
        
        mock_uow.users.get_by_email.return_value = None
        
        # Act
        result = await user_use_cases.verify_user_password(email, password)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_verify_user_password_wrong_password(self, user_use_cases, mock_uow):
        """Test password verification with wrong password."""
        # Arrange
        email = "test@example.com"
        password = "wrongpassword"
        
        user = UserFactory.create_user(email=email, password="password123")
        mock_uow.users.get_by_email.return_value = user
        
        # Act
        result = await user_use_cases.verify_user_password(email, password)
        
        # Assert
        assert result is None