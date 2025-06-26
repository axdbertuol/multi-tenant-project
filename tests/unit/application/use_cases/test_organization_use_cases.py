import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4
from src.application.use_cases.organization_use_cases import OrganizationUseCases
from src.application.dtos.organization_dto import (
    CreateOrganizationDto,
    UpdateOrganizationDto,
    TransferOwnershipDto,
    AddUserToOrganizationDto
)
from tests.factories.organization_factory import OrganizationFactory
from tests.factories.user_factory import UserFactory


class TestOrganizationUseCases:
    """Unit tests for OrganizationUseCases."""
    
    @pytest.fixture
    def mock_uow(self):
        """Mock Unit of Work."""
        uow = Mock()
        uow.organizations = AsyncMock()
        uow.users = AsyncMock()
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        return uow
    
    @pytest.fixture
    def organization_use_cases(self, mock_uow):
        """Create OrganizationUseCases instance with mocked dependencies."""
        return OrganizationUseCases(mock_uow)
    
    @pytest.mark.asyncio
    async def test_create_organization_success(self, organization_use_cases, mock_uow):
        """Test successful organization creation."""
        # Arrange
        owner_id = uuid4()
        create_dto = CreateOrganizationDto(
            name="Test Organization",
            description="Test description"
        )
        
        owner_user = UserFactory.create_user()
        mock_uow.organizations.get_by_name.return_value = None  # No existing org
        mock_uow.users.get_by_id.return_value = owner_user  # Owner exists
        
        created_org = OrganizationFactory.create_organization(
            name="Test Organization",
            owner_id=owner_id,
            description="Test description"
        )
        mock_uow.organizations.create.return_value = created_org
        mock_uow.organizations.add_user_to_organization.return_value = None
        
        # Act
        result = await organization_use_cases.create_organization(owner_id, create_dto)
        
        # Assert
        assert result.name == "Test Organization"
        assert result.description == "Test description"
        assert result.owner_id == owner_id
        assert result.is_active is True
        mock_uow.organizations.add_user_to_organization.assert_called_once_with(created_org.id, owner_id)
    
    @pytest.mark.asyncio
    async def test_create_organization_duplicate_name(self, organization_use_cases, mock_uow):
        """Test organization creation with duplicate name."""
        # Arrange
        owner_id = uuid4()
        create_dto = CreateOrganizationDto(name="Existing Org")
        
        existing_org = OrganizationFactory.create_organization(name="Existing Org")
        mock_uow.organizations.get_by_name.return_value = existing_org
        
        # Act & Assert
        with pytest.raises(ValueError, match="Organization with name Existing Org already exists"):
            await organization_use_cases.create_organization(owner_id, create_dto)
    
    @pytest.mark.asyncio
    async def test_create_organization_invalid_owner(self, organization_use_cases, mock_uow):
        """Test organization creation with non-existent owner."""
        # Arrange
        owner_id = uuid4()
        create_dto = CreateOrganizationDto(name="Test Org")
        
        mock_uow.organizations.get_by_name.return_value = None
        mock_uow.users.get_by_id.return_value = None  # Owner doesn't exist
        
        # Act & Assert
        with pytest.raises(ValueError, match=f"User with id {owner_id} does not exist"):
            await organization_use_cases.create_organization(owner_id, create_dto)
    
    @pytest.mark.asyncio
    async def test_get_organization_by_id_success(self, organization_use_cases, mock_uow):
        """Test getting organization by ID successfully."""
        # Arrange
        org_id = uuid4()
        org = OrganizationFactory.create_organization()
        mock_uow.organizations.get_by_id.return_value = org
        
        # Act
        result = await organization_use_cases.get_organization_by_id(org_id)
        
        # Assert
        assert result is not None
        assert result.id == org.id
        assert result.name == org.name
    
    @pytest.mark.asyncio
    async def test_get_organization_by_id_not_found(self, organization_use_cases, mock_uow):
        """Test getting non-existent organization by ID."""
        # Arrange
        org_id = uuid4()
        mock_uow.organizations.get_by_id.return_value = None
        
        # Act
        result = await organization_use_cases.get_organization_by_id(org_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_organization_by_name_success(self, organization_use_cases, mock_uow):
        """Test getting organization by name successfully."""
        # Arrange
        org = OrganizationFactory.create_organization(name="Test Org")
        mock_uow.organizations.get_by_name.return_value = org
        
        # Act
        result = await organization_use_cases.get_organization_by_name("Test Org")
        
        # Assert
        assert result is not None
        assert result.name == "Test Org"
        assert result.id == org.id
    
    @pytest.mark.asyncio
    async def test_get_organizations_by_owner(self, organization_use_cases, mock_uow):
        """Test getting organizations by owner ID."""
        # Arrange
        owner_id = uuid4()
        orgs = [
            OrganizationFactory.create_organization(owner_id=owner_id),
            OrganizationFactory.create_organization(owner_id=owner_id)
        ]
        mock_uow.organizations.get_by_owner_id.return_value = orgs
        
        # Act
        result = await organization_use_cases.get_organizations_by_owner(owner_id)
        
        # Assert
        assert len(result) == 2
        assert all(org_dto.owner_id == owner_id for org_dto in result)
    
    @pytest.mark.asyncio
    async def test_get_user_organizations(self, organization_use_cases, mock_uow):
        """Test getting organizations for a user."""
        # Arrange
        user_id = uuid4()
        orgs = [
            OrganizationFactory.create_organization(),
            OrganizationFactory.create_organization()
        ]
        mock_uow.organizations.get_organizations_by_user_id.return_value = orgs
        
        # Act
        result = await organization_use_cases.get_user_organizations(user_id)
        
        # Assert
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_update_organization_success(self, organization_use_cases, mock_uow):
        """Test successful organization update."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        update_dto = UpdateOrganizationDto(
            name="Updated Name",
            description="Updated description"
        )
        
        original_org = OrganizationFactory.create_organization(
            name="Original Name",
            owner_id=owner_id
        )
        updated_org = original_org.update_name("Updated Name").update_description("Updated description")
        
        mock_uow.organizations.get_by_id.return_value = original_org
        mock_uow.organizations.get_by_name.return_value = None  # Name not taken
        mock_uow.organizations.update.return_value = updated_org
        
        # Act
        result = await organization_use_cases.update_organization(org_id, update_dto, owner_id)
        
        # Assert
        assert result is not None
        assert result.name == "Updated Name"
        assert result.description == "Updated description"
    
    @pytest.mark.asyncio
    async def test_update_organization_not_owner(self, organization_use_cases, mock_uow):
        """Test organization update by non-owner."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        non_owner_id = uuid4()
        update_dto = UpdateOrganizationDto(name="Updated Name")
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        mock_uow.organizations.get_by_id.return_value = org
        
        # Act & Assert
        with pytest.raises(PermissionError, match="Only the organization owner can update the organization"):
            await organization_use_cases.update_organization(org_id, update_dto, non_owner_id)
    
    @pytest.mark.asyncio
    async def test_update_organization_duplicate_name(self, organization_use_cases, mock_uow):
        """Test organization update with duplicate name."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        update_dto = UpdateOrganizationDto(name="Existing Name")
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        existing_org = OrganizationFactory.create_organization(name="Existing Name")
        
        mock_uow.organizations.get_by_id.return_value = org
        mock_uow.organizations.get_by_name.return_value = existing_org
        
        # Act & Assert
        with pytest.raises(ValueError, match="Organization with name Existing Name already exists"):
            await organization_use_cases.update_organization(org_id, update_dto, owner_id)
    
    @pytest.mark.asyncio
    async def test_transfer_ownership_success(self, organization_use_cases, mock_uow):
        """Test successful ownership transfer."""
        # Arrange
        org_id = uuid4()
        current_owner_id = uuid4()
        new_owner_id = uuid4()
        transfer_dto = TransferOwnershipDto(new_owner_id=new_owner_id)
        
        org = OrganizationFactory.create_organization(owner_id=current_owner_id)
        new_owner = UserFactory.create_user()
        transferred_org = org.transfer_ownership(new_owner_id)
        
        mock_uow.organizations.get_by_id.return_value = org
        mock_uow.users.get_by_id.return_value = new_owner
        mock_uow.organizations.is_user_in_organization.return_value = False
        mock_uow.organizations.add_user_to_organization.return_value = None
        mock_uow.organizations.update.return_value = transferred_org
        
        # Act
        result = await organization_use_cases.transfer_ownership(org_id, transfer_dto, current_owner_id)
        
        # Assert
        assert result is not None
        assert result.owner_id == new_owner_id
        mock_uow.organizations.add_user_to_organization.assert_called_once_with(org_id, new_owner_id)
    
    @pytest.mark.asyncio
    async def test_transfer_ownership_not_owner(self, organization_use_cases, mock_uow):
        """Test ownership transfer by non-owner."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        non_owner_id = uuid4()
        new_owner_id = uuid4()
        transfer_dto = TransferOwnershipDto(new_owner_id=new_owner_id)
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        mock_uow.organizations.get_by_id.return_value = org
        
        # Act & Assert
        with pytest.raises(PermissionError, match="Only the current owner can transfer ownership"):
            await organization_use_cases.transfer_ownership(org_id, transfer_dto, non_owner_id)
    
    @pytest.mark.asyncio
    async def test_transfer_ownership_invalid_new_owner(self, organization_use_cases, mock_uow):
        """Test ownership transfer to non-existent user."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        new_owner_id = uuid4()
        transfer_dto = TransferOwnershipDto(new_owner_id=new_owner_id)
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        mock_uow.organizations.get_by_id.return_value = org
        mock_uow.users.get_by_id.return_value = None  # New owner doesn't exist
        
        # Act & Assert
        with pytest.raises(ValueError, match=f"User with id {new_owner_id} does not exist"):
            await organization_use_cases.transfer_ownership(org_id, transfer_dto, owner_id)
    
    @pytest.mark.asyncio
    async def test_add_user_to_organization_success(self, organization_use_cases, mock_uow):
        """Test successfully adding user to organization."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()
        add_user_dto = AddUserToOrganizationDto(user_id=user_id)
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        user = UserFactory.create_user()
        
        mock_uow.organizations.get_by_id.return_value = org
        mock_uow.users.get_by_id.return_value = user
        mock_uow.organizations.is_user_in_organization.return_value = False
        mock_uow.organizations.add_user_to_organization.return_value = None
        
        # Act
        result = await organization_use_cases.add_user_to_organization(org_id, add_user_dto, owner_id)
        
        # Assert
        assert result is True
        mock_uow.organizations.add_user_to_organization.assert_called_once_with(org_id, user_id)
    
    @pytest.mark.asyncio
    async def test_add_user_to_organization_not_owner(self, organization_use_cases, mock_uow):
        """Test adding user to organization by non-owner."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        non_owner_id = uuid4()
        user_id = uuid4()
        add_user_dto = AddUserToOrganizationDto(user_id=user_id)
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        mock_uow.organizations.get_by_id.return_value = org
        
        # Act & Assert
        with pytest.raises(PermissionError, match="Only the organization owner can add users"):
            await organization_use_cases.add_user_to_organization(org_id, add_user_dto, non_owner_id)
    
    @pytest.mark.asyncio
    async def test_add_user_to_organization_already_member(self, organization_use_cases, mock_uow):
        """Test adding user who is already a member."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()
        add_user_dto = AddUserToOrganizationDto(user_id=user_id)
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        user = UserFactory.create_user()
        
        mock_uow.organizations.get_by_id.return_value = org
        mock_uow.users.get_by_id.return_value = user
        mock_uow.organizations.is_user_in_organization.return_value = True  # Already member
        
        # Act & Assert
        with pytest.raises(ValueError, match="User is already a member of this organization"):
            await organization_use_cases.add_user_to_organization(org_id, add_user_dto, owner_id)
    
    @pytest.mark.asyncio
    async def test_remove_user_from_organization_by_owner(self, organization_use_cases, mock_uow):
        """Test removing user from organization by owner."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        
        mock_uow.organizations.get_by_id.return_value = org
        mock_uow.organizations.is_user_in_organization.return_value = True
        mock_uow.organizations.remove_user_from_organization.return_value = None
        
        # Act
        result = await organization_use_cases.remove_user_from_organization(org_id, user_id, owner_id)
        
        # Assert
        assert result is True
        mock_uow.organizations.remove_user_from_organization.assert_called_once_with(org_id, user_id)
    
    @pytest.mark.asyncio
    async def test_remove_user_from_organization_by_self(self, organization_use_cases, mock_uow):
        """Test user removing themselves from organization."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        
        mock_uow.organizations.get_by_id.return_value = org
        mock_uow.organizations.is_user_in_organization.return_value = True
        mock_uow.organizations.remove_user_from_organization.return_value = None
        
        # Act (user removing themselves)
        result = await organization_use_cases.remove_user_from_organization(org_id, user_id, user_id)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_remove_user_from_organization_cannot_remove_owner(self, organization_use_cases, mock_uow):
        """Test that owner cannot be removed from organization."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        mock_uow.organizations.get_by_id.return_value = org
        
        # Act & Assert (trying to remove owner)
        with pytest.raises(ValueError, match="The organization owner cannot be removed from the organization"):
            await organization_use_cases.remove_user_from_organization(org_id, owner_id, owner_id)
    
    @pytest.mark.asyncio
    async def test_remove_user_not_member(self, organization_use_cases, mock_uow):
        """Test removing user who is not a member."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        
        mock_uow.organizations.get_by_id.return_value = org
        mock_uow.organizations.is_user_in_organization.return_value = False  # Not member
        
        # Act & Assert
        with pytest.raises(ValueError, match="User is not a member of this organization"):
            await organization_use_cases.remove_user_from_organization(org_id, user_id, owner_id)
    
    @pytest.mark.asyncio
    async def test_deactivate_organization_success(self, organization_use_cases, mock_uow):
        """Test successful organization deactivation."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        deactivated_org = org.deactivate()
        
        mock_uow.organizations.get_by_id.return_value = org
        mock_uow.organizations.update.return_value = deactivated_org
        
        # Act
        result = await organization_use_cases.deactivate_organization(org_id, owner_id)
        
        # Assert
        assert result is not None
        assert result.is_active is False
    
    @pytest.mark.asyncio
    async def test_deactivate_organization_not_owner(self, organization_use_cases, mock_uow):
        """Test organization deactivation by non-owner."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        non_owner_id = uuid4()
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        mock_uow.organizations.get_by_id.return_value = org
        
        # Act & Assert
        with pytest.raises(PermissionError, match="Only the organization owner can deactivate the organization"):
            await organization_use_cases.deactivate_organization(org_id, non_owner_id)
    
    @pytest.mark.asyncio
    async def test_activate_organization_success(self, organization_use_cases, mock_uow):
        """Test successful organization activation."""
        # Arrange
        org_id = uuid4()
        owner_id = uuid4()
        
        org = OrganizationFactory.create_organization(owner_id=owner_id)
        deactivated_org = org.deactivate()
        activated_org = deactivated_org.activate()
        
        mock_uow.organizations.get_by_id.return_value = deactivated_org
        mock_uow.organizations.update.return_value = activated_org
        
        # Act
        result = await organization_use_cases.activate_organization(org_id, owner_id)
        
        # Assert
        assert result is not None
        assert result.is_active is True