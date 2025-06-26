import pytest
from uuid import uuid4
from src.domain.entities.organization import Organization
from src.infrastructure.repositories.organization_repository_impl import OrganizationRepositoryImpl
from tests.factories.organization_factory import OrganizationFactory
from tests.factories.user_factory import UserFactory


@pytest.mark.integration
class TestOrganizationRepositoryImpl:
    """Integration tests for OrganizationRepositoryImpl."""
    
    @pytest.fixture
    def organization_repository(self, db_session):
        """Create OrganizationRepositoryImpl instance with test database session."""
        return OrganizationRepositoryImpl(db_session)
    
    @pytest.fixture
    async def sample_user(self, unit_of_work):
        """Create a sample user for testing organization ownership."""
        user = UserFactory.create_user(email="owner@example.com")
        async with unit_of_work:
            created_user = await unit_of_work.users.create(user)
            return created_user
    
    @pytest.mark.asyncio
    async def test_create_organization(self, organization_repository, sample_user):
        """Test creating an organization in the database."""
        # Arrange
        org = OrganizationFactory.create_organization(
            name="Test Organization",
            owner_id=sample_user.id,
            description="Test organization description"
        )
        
        # Act
        created_org = await organization_repository.create(org)
        
        # Assert
        assert created_org.id == org.id
        assert created_org.name == "Test Organization"
        assert created_org.description == "Test organization description"
        assert created_org.owner_id == sample_user.id
        assert created_org.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_by_id_existing_organization(self, organization_repository, sample_user):
        """Test getting an existing organization by ID."""
        # Arrange
        org = OrganizationFactory.create_organization(owner_id=sample_user.id)
        created_org = await organization_repository.create(org)
        
        # Act
        retrieved_org = await organization_repository.get_by_id(created_org.id)
        
        # Assert
        assert retrieved_org is not None
        assert retrieved_org.id == created_org.id
        assert retrieved_org.name == created_org.name
        assert retrieved_org.owner_id == sample_user.id
    
    @pytest.mark.asyncio
    async def test_get_by_id_non_existent_organization(self, organization_repository):
        """Test getting a non-existent organization by ID."""
        # Arrange
        non_existent_id = uuid4()
        
        # Act
        result = await organization_repository.get_by_id(non_existent_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_name_existing_organization(self, organization_repository, sample_user):
        """Test getting an existing organization by name."""
        # Arrange
        org = OrganizationFactory.create_organization(
            name="Unique Org Name",
            owner_id=sample_user.id
        )
        await organization_repository.create(org)
        
        # Act
        retrieved_org = await organization_repository.get_by_name("Unique Org Name")
        
        # Assert
        assert retrieved_org is not None
        assert retrieved_org.name == "Unique Org Name"
        assert retrieved_org.id == org.id
    
    @pytest.mark.asyncio
    async def test_get_by_name_non_existent_organization(self, organization_repository):
        """Test getting a non-existent organization by name."""
        # Act
        result = await organization_repository.get_by_name("Non Existent Org")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_owner_id(self, organization_repository, sample_user):
        """Test getting organizations by owner ID."""
        # Arrange
        orgs = [
            OrganizationFactory.create_organization(name="Org 1", owner_id=sample_user.id),
            OrganizationFactory.create_organization(name="Org 2", owner_id=sample_user.id),
            OrganizationFactory.create_organization(name="Org 3", owner_id=sample_user.id)
        ]
        
        for org in orgs:
            await organization_repository.create(org)
        
        # Act
        owner_orgs = await organization_repository.get_by_owner_id(sample_user.id)
        
        # Assert
        assert len(owner_orgs) == 3
        org_names = [org.name for org in owner_orgs]
        assert "Org 1" in org_names
        assert "Org 2" in org_names
        assert "Org 3" in org_names
    
    @pytest.mark.asyncio
    async def test_get_by_owner_id_no_organizations(self, organization_repository):
        """Test getting organizations for owner with no organizations."""
        # Arrange
        non_owner_id = uuid4()
        
        # Act
        result = await organization_repository.get_by_owner_id(non_owner_id)
        
        # Assert
        assert result == []
    
    @pytest.mark.asyncio
    async def test_update_organization(self, organization_repository, sample_user):
        """Test updating an organization."""
        # Arrange
        org = OrganizationFactory.create_organization(
            name="Original Name",
            owner_id=sample_user.id
        )
        created_org = await organization_repository.create(org)
        
        # Update the organization
        updated_org = created_org.update_name("Updated Name")
        
        # Act
        result = await organization_repository.update(updated_org)
        
        # Assert
        assert result.name == "Updated Name"
        assert result.updated_at is not None
        assert result.id == created_org.id
        
        # Verify in database
        retrieved_org = await organization_repository.get_by_id(created_org.id)
        assert retrieved_org.name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_update_organization_description(self, organization_repository, sample_user):
        """Test updating an organization's description."""
        # Arrange
        org = OrganizationFactory.create_organization(
            description="Original description",
            owner_id=sample_user.id
        )
        created_org = await organization_repository.create(org)
        
        # Update description
        updated_org = created_org.update_description("Updated description")
        
        # Act
        result = await organization_repository.update(updated_org)
        
        # Assert
        assert result.description == "Updated description"
        assert result.updated_at is not None
        
        # Verify in database
        retrieved_org = await organization_repository.get_by_id(created_org.id)
        assert retrieved_org.description == "Updated description"
    
    @pytest.mark.asyncio
    async def test_transfer_ownership(self, organization_repository, unit_of_work):
        """Test transferring organization ownership."""
        # Arrange
        async with unit_of_work:
            original_owner = await unit_of_work.users.create(
                UserFactory.create_user(email="original@example.com")
            )
            new_owner = await unit_of_work.users.create(
                UserFactory.create_user(email="new@example.com")
            )
        
        org = OrganizationFactory.create_organization(owner_id=original_owner.id)
        created_org = await organization_repository.create(org)
        
        # Transfer ownership
        transferred_org = created_org.transfer_ownership(new_owner.id)
        
        # Act
        result = await organization_repository.update(transferred_org)
        
        # Assert
        assert result.owner_id == new_owner.id
        assert result.updated_at is not None
        
        # Verify in database
        retrieved_org = await organization_repository.get_by_id(created_org.id)
        assert retrieved_org.owner_id == new_owner.id
    
    @pytest.mark.asyncio
    async def test_delete_organization(self, organization_repository, sample_user):
        """Test deleting an organization."""
        # Arrange
        org = OrganizationFactory.create_organization(owner_id=sample_user.id)
        created_org = await organization_repository.create(org)
        
        # Act
        result = await organization_repository.delete(created_org.id)
        
        # Assert
        assert result is True
        
        # Verify organization is deleted
        deleted_org = await organization_repository.get_by_id(created_org.id)
        assert deleted_org is None
    
    @pytest.mark.asyncio
    async def test_delete_non_existent_organization(self, organization_repository):
        """Test deleting a non-existent organization."""
        # Arrange
        non_existent_id = uuid4()
        
        # Act
        result = await organization_repository.delete(non_existent_id)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_add_user_to_organization(self, organization_repository, unit_of_work):
        """Test adding a user to an organization."""
        # Arrange
        async with unit_of_work:
            owner = await unit_of_work.users.create(
                UserFactory.create_user(email="owner@example.com")
            )
            member = await unit_of_work.users.create(
                UserFactory.create_user(email="member@example.com")
            )
        
        org = OrganizationFactory.create_organization(owner_id=owner.id)
        created_org = await organization_repository.create(org)
        
        # Act
        await organization_repository.add_user_to_organization(created_org.id, member.id)
        
        # Assert
        is_member = await organization_repository.is_user_in_organization(created_org.id, member.id)
        assert is_member is True
    
    @pytest.mark.asyncio
    async def test_remove_user_from_organization(self, organization_repository, unit_of_work):
        """Test removing a user from an organization."""
        # Arrange
        async with unit_of_work:
            owner = await unit_of_work.users.create(
                UserFactory.create_user(email="owner@example.com")
            )
            member = await unit_of_work.users.create(
                UserFactory.create_user(email="member@example.com")
            )
        
        org = OrganizationFactory.create_organization(owner_id=owner.id)
        created_org = await organization_repository.create(org)
        
        # Add user first
        await organization_repository.add_user_to_organization(created_org.id, member.id)
        
        # Act
        await organization_repository.remove_user_from_organization(created_org.id, member.id)
        
        # Assert
        is_member = await organization_repository.is_user_in_organization(created_org.id, member.id)
        assert is_member is False
    
    @pytest.mark.asyncio
    async def test_is_user_in_organization_true(self, organization_repository, unit_of_work):
        """Test checking if user is in organization - true case."""
        # Arrange
        async with unit_of_work:
            owner = await unit_of_work.users.create(
                UserFactory.create_user(email="owner@example.com")
            )
            member = await unit_of_work.users.create(
                UserFactory.create_user(email="member@example.com")
            )
        
        org = OrganizationFactory.create_organization(owner_id=owner.id)
        created_org = await organization_repository.create(org)
        
        # Add user to organization
        await organization_repository.add_user_to_organization(created_org.id, member.id)
        
        # Act
        result = await organization_repository.is_user_in_organization(created_org.id, member.id)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_is_user_in_organization_false(self, organization_repository, unit_of_work):
        """Test checking if user is in organization - false case."""
        # Arrange
        async with unit_of_work:
            owner = await unit_of_work.users.create(
                UserFactory.create_user(email="owner@example.com")
            )
            non_member = await unit_of_work.users.create(
                UserFactory.create_user(email="nonmember@example.com")
            )
        
        org = OrganizationFactory.create_organization(owner_id=owner.id)
        created_org = await organization_repository.create(org)
        
        # Act (without adding user to organization)
        result = await organization_repository.is_user_in_organization(created_org.id, non_member.id)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_organizations_by_user_id(self, organization_repository, unit_of_work):
        """Test getting organizations by user membership."""
        # Arrange
        async with unit_of_work:
            owner1 = await unit_of_work.users.create(
                UserFactory.create_user(email="owner1@example.com")
            )
            owner2 = await unit_of_work.users.create(
                UserFactory.create_user(email="owner2@example.com")
            )
            member = await unit_of_work.users.create(
                UserFactory.create_user(email="member@example.com")
            )
        
        # Create organizations
        org1 = OrganizationFactory.create_organization(name="Org 1", owner_id=owner1.id)
        org2 = OrganizationFactory.create_organization(name="Org 2", owner_id=owner2.id)
        org3 = OrganizationFactory.create_organization(name="Org 3", owner_id=owner1.id)
        
        created_org1 = await organization_repository.create(org1)
        created_org2 = await organization_repository.create(org2)
        created_org3 = await organization_repository.create(org3)
        
        # Add member to org1 and org2 only
        await organization_repository.add_user_to_organization(created_org1.id, member.id)
        await organization_repository.add_user_to_organization(created_org2.id, member.id)
        
        # Act
        member_orgs = await organization_repository.get_organizations_by_user_id(member.id)
        
        # Assert
        assert len(member_orgs) == 2
        org_names = [org.name for org in member_orgs]
        assert "Org 1" in org_names
        assert "Org 2" in org_names
        assert "Org 3" not in org_names
    
    @pytest.mark.asyncio
    async def test_get_organizations_by_user_id_no_memberships(self, organization_repository, unit_of_work):
        """Test getting organizations for user with no memberships."""
        # Arrange
        async with unit_of_work:
            user = await unit_of_work.users.create(
                UserFactory.create_user(email="nomember@example.com")
            )
        
        # Act
        result = await organization_repository.get_organizations_by_user_id(user.id)
        
        # Assert
        assert result == []
    
    @pytest.mark.asyncio
    async def test_organization_activation_status(self, organization_repository, sample_user):
        """Test updating organization activation status."""
        # Arrange
        org = OrganizationFactory.create_organization(owner_id=sample_user.id)
        created_org = await organization_repository.create(org)
        
        # Deactivate organization
        deactivated_org = created_org.deactivate()
        
        # Act
        result = await organization_repository.update(deactivated_org)
        
        # Assert
        assert result.is_active is False
        assert result.updated_at is not None
        
        # Verify in database
        retrieved_org = await organization_repository.get_by_id(created_org.id)
        assert retrieved_org.is_active is False
    
    @pytest.mark.asyncio
    async def test_organization_timestamps(self, organization_repository, sample_user):
        """Test that organization timestamps are properly handled."""
        # Arrange
        org = OrganizationFactory.create_organization(owner_id=sample_user.id)
        
        # Act
        created_org = await organization_repository.create(org)
        
        # Assert
        assert created_org.created_at is not None
        assert created_org.updated_at is None
        
        # Update organization and check updated_at
        updated_org = created_org.update_name("New Name")
        result = await organization_repository.update(updated_org)
        
        assert result.updated_at is not None
        assert result.updated_at > result.created_at
    
    @pytest.mark.asyncio
    async def test_domain_model_mapping(self, organization_repository, sample_user):
        """Test that domain entities are properly mapped to/from database models."""
        # Arrange
        org = OrganizationFactory.create_organization(
            name="Mapping Test Org",
            description="Test mapping description",
            owner_id=sample_user.id
        )
        
        # Act - Create and retrieve
        created_org = await organization_repository.create(org)
        retrieved_org = await organization_repository.get_by_id(created_org.id)
        
        # Assert - All domain properties preserved
        assert isinstance(retrieved_org, Organization)
        assert retrieved_org.id == org.id
        assert retrieved_org.name == "Mapping Test Org"
        assert retrieved_org.description == "Test mapping description"
        assert retrieved_org.owner_id == sample_user.id
        assert retrieved_org.is_active == org.is_active
        assert retrieved_org.created_at == created_org.created_at