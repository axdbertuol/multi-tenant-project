import pytest
from uuid import uuid4
from src.application.use_cases.organization_use_cases import OrganizationUseCases
from src.application.dtos.organization_dto import (
    CreateOrganizationDto,
    UpdateOrganizationDto,
    TransferOwnershipDto,
    AddUserToOrganizationDto
)
from tests.factories.user_factory import UserFactory
from tests.factories.organization_factory import OrganizationFactory


@pytest.mark.integration
class TestOrganizationUseCasesIntegration:
    """Integration tests for OrganizationUseCases with real database."""
    
    @pytest.fixture
    def organization_use_cases(self, unit_of_work):
        """Create OrganizationUseCases instance with test unit of work."""
        return OrganizationUseCases(unit_of_work)
    
    @pytest.fixture
     def sample_owner(self, unit_of_work):
        """Create a sample user to act as organization owner."""
        user = UserFactory.create_user(email="owner@example.com")
         with unit_of_work:
            return  unit_of_work.users.create(user)
    
    @pytest.fixture
     def sample_user(self, unit_of_work):
        """Create a sample user for testing memberships."""
        user = UserFactory.create_user(email="member@example.com")
         with unit_of_work:
            return  unit_of_work.users.create(user)
    
    @pytest.mark.io
     def test_create_organization_full_flow(self, organization_use_cases, sample_owner):
        """Test complete organization creation flow."""
        # Arrange
        create_dto = CreateOrganizationDto(
            name="Integration Test Org",
            description="Test organization for integration testing"
        )
        
        # Act
        result =  organization_use_cases.create_organization(sample_owner.id, create_dto)
        
        # Assert
        assert result is not None
        assert result.name == "Integration Test Org"
        assert result.description == "Test organization for integration testing"
        assert result.owner_id == sample_owner.id
        assert result.is_active is True
        
        # Verify owner is automatically added as member
        member_orgs =  organization_use_cases.get_user_organizations(sample_owner.id)
        assert len(member_orgs) == 1
        assert member_orgs[0].id == result.id
    
    @pytest.mark.io
     def test_organization_lifecycle(self, organization_use_cases, sample_owner):
        """Test complete organization lifecycle: create, update, deactivate, activate."""
        # Create
        create_dto = CreateOrganizationDto(name="Lifecycle Org", description="Original description")
        created_org =  organization_use_cases.create_organization(sample_owner.id, create_dto)
        
        # Update
        update_dto = UpdateOrganizationDto(name="Updated Lifecycle Org", description="Updated description")
        updated_org =  organization_use_cases.update_organization(
            created_org.id, update_dto, sample_owner.id
        )
        assert updated_org.name == "Updated Lifecycle Org"
        assert updated_org.description == "Updated description"
        
        # Deactivate
        deactivated_org =  organization_use_cases.deactivate_organization(
            created_org.id, sample_owner.id
        )
        assert deactivated_org.is_active is False
        
        # Activate
        activated_org =  organization_use_cases.activate_organization(
            created_org.id, sample_owner.id
        )
        assert activated_org.is_active is True
    
    @pytest.mark.io
     def test_ownership_transfer_flow(self, organization_use_cases, unit_of_work):
        """Test complete ownership transfer flow."""
        # Create users
         with unit_of_work:
            original_owner =  unit_of_work.users.create(
                UserFactory.create_user(email="original@example.com")
            )
            new_owner =  unit_of_work.users.create(
                UserFactory.create_user(email="newowner@example.com")
            )
        
        # Create organization
        create_dto = CreateOrganizationDto(name="Transfer Test Org")
        org =  organization_use_cases.create_organization(original_owner.id, create_dto)
        
        # Transfer ownership
        transfer_dto = TransferOwnershipDto(new_owner_id=new_owner.id)
        transferred_org =  organization_use_cases.transfer_ownership(
            org.id, transfer_dto, original_owner.id
        )
        
        # Assert
        assert transferred_org.owner_id == new_owner.id
        
        # Verify new owner can update organization
        update_dto = UpdateOrganizationDto(name="Updated by New Owner")
        updated_org =  organization_use_cases.update_organization(
            org.id, update_dto, new_owner.id
        )
        assert updated_org.name == "Updated by New Owner"
        
        # Verify original owner can no longer update
        with pytest.raises(PermissionError):
             organization_use_cases.update_organization(
                org.id, UpdateOrganizationDto(name="Should Fail"), original_owner.id
            )
    
    @pytest.mark.io
     def test_user_membership_management(self, organization_use_cases, unit_of_work):
        """Test complete user membership management flow."""
        # Create users
         with unit_of_work:
            owner =  unit_of_work.users.create(
                UserFactory.create_user(email="owner@example.com")
            )
            user1 =  unit_of_work.users.create(
                UserFactory.create_user(email="user1@example.com")
            )
            user2 =  unit_of_work.users.create(
                UserFactory.create_user(email="user2@example.com")
            )
        
        # Create organization
        create_dto = CreateOrganizationDto(name="Membership Test Org")
        org =  organization_use_cases.create_organization(owner.id, create_dto)
        
        # Add users to organization
        add_user1_dto = AddUserToOrganizationDto(user_id=user1.id)
        add_user2_dto = AddUserToOrganizationDto(user_id=user2.id)
        
        result1 =  organization_use_cases.add_user_to_organization(org.id, add_user1_dto, owner.id)
        result2 =  organization_use_cases.add_user_to_organization(org.id, add_user2_dto, owner.id)
        
        assert result1 is True
        assert result2 is True
        
        # Verify memberships
        user1_orgs =  organization_use_cases.get_user_organizations(user1.id)
        user2_orgs =  organization_use_cases.get_user_organizations(user2.id)
        
        assert len(user1_orgs) == 1
        assert len(user2_orgs) == 1
        assert user1_orgs[0].id == org.id
        assert user2_orgs[0].id == org.id
        
        # Remove user1 (by owner)
        result =  organization_use_cases.remove_user_from_organization(org.id, user1.id, owner.id)
        assert result is True
        
        # Remove user2 (by themselves)
        result =  organization_use_cases.remove_user_from_organization(org.id, user2.id, user2.id)
        assert result is True
        
        # Verify removals
        user1_orgs_after =  organization_use_cases.get_user_organizations(user1.id)
        user2_orgs_after =  organization_use_cases.get_user_organizations(user2.id)
        
        assert len(user1_orgs_after) == 0
        assert len(user2_orgs_after) == 0
    
    @pytest.mark.io
     def test_multiple_organizations_same_owner(self, organization_use_cases, sample_owner):
        """Test owner having multiple organizations."""
        # Create multiple organizations
        orgs = []
        for i in range(3):
            create_dto = CreateOrganizationDto(name=f"Multi Org {i+1}")
            org =  organization_use_cases.create_organization(sample_owner.id, create_dto)
            orgs.append(org)
        
        # Verify owner has all organizations
        owner_orgs =  organization_use_cases.get_organizations_by_owner(sample_owner.id)
        assert len(owner_orgs) == 3
        
        org_names = [org.name for org in owner_orgs]
        assert "Multi Org 1" in org_names
        assert "Multi Org 2" in org_names
        assert "Multi Org 3" in org_names
        
        # Verify owner is member of all organizations
        member_orgs =  organization_use_cases.get_user_organizations(sample_owner.id)
        assert len(member_orgs) == 3
    
    @pytest.mark.io
     def test_user_multiple_organization_memberships(self, organization_use_cases, unit_of_work):
        """Test user being member of multiple organizations."""
        # Create multiple owners and a member
         with unit_of_work:
            owner1 =  unit_of_work.users.create(
                UserFactory.create_user(email="owner1@example.com")
            )
            owner2 =  unit_of_work.users.create(
                UserFactory.create_user(email="owner2@example.com")
            )
            member =  unit_of_work.users.create(
                UserFactory.create_user(email="member@example.com")
            )
        
        # Create organizations
        org1 =  organization_use_cases.create_organization(
            owner1.id, CreateOrganizationDto(name="Org 1")
        )
        org2 =  organization_use_cases.create_organization(
            owner2.id, CreateOrganizationDto(name="Org 2")
        )
        
        # Add member to both organizations
         organization_use_cases.add_user_to_organization(
            org1.id, AddUserToOrganizationDto(user_id=member.id), owner1.id
        )
         organization_use_cases.add_user_to_organization(
            org2.id, AddUserToOrganizationDto(user_id=member.id), owner2.id
        )
        
        # Verify member is in both organizations
        member_orgs =  organization_use_cases.get_user_organizations(member.id)
        assert len(member_orgs) == 2
        
        org_names = [org.name for org in member_orgs]
        assert "Org 1" in org_names
        assert "Org 2" in org_names
    
    @pytest.mark.io
     def test_error_scenarios_and_rollback(self, organization_use_cases, unit_of_work):
        """Test error scenarios and transaction rollback."""
        # Create owner
         with unit_of_work:
            owner =  unit_of_work.users.create(
                UserFactory.create_user(email="error@example.com")
            )
        
        # Test: Create organization with duplicate name
        org1 =  organization_use_cases.create_organization(
            owner.id, CreateOrganizationDto(name="Duplicate Name Org")
        )
        
        with pytest.raises(ValueError, match="Organization with name Duplicate Name Org already exists"):
             organization_use_cases.create_organization(
                owner.id, CreateOrganizationDto(name="Duplicate Name Org")
            )
        
        # Test: Update with non-existent organization
        non_existent_id = uuid4()
        result =  organization_use_cases.update_organization(
            non_existent_id, UpdateOrganizationDto(name="Should Fail"), owner.id
        )
        assert result is None
        
        # Test: Add non-existent user to organization
        with pytest.raises(ValueError, match="does not exist"):
             organization_use_cases.add_user_to_organization(
                org1.id, AddUserToOrganizationDto(user_id=uuid4()), owner.id
            )
    
    @pytest.mark.io
     def test_permission_enforcement(self, organization_use_cases, unit_of_work):
        """Test permission enforcement across different operations."""
        # Create users
         with unit_of_work:
            owner =  unit_of_work.users.create(
                UserFactory.create_user(email="owner@example.com")
            )
            non_owner =  unit_of_work.users.create(
                UserFactory.create_user(email="nonowner@example.com")
            )
        
        # Create organization
        org =  organization_use_cases.create_organization(
            owner.id, CreateOrganizationDto(name="Permission Test Org")
        )
        
        # Test: Non-owner cannot update
        with pytest.raises(PermissionError):
             organization_use_cases.update_organization(
                org.id, UpdateOrganizationDto(name="Unauthorized Update"), non_owner.id
            )
        
        # Test: Non-owner cannot add users
        with pytest.raises(PermissionError):
             organization_use_cases.add_user_to_organization(
                org.id, AddUserToOrganizationDto(user_id=non_owner.id), non_owner.id
            )
        
        # Test: Non-owner cannot transfer ownership
        with pytest.raises(PermissionError):
             organization_use_cases.transfer_ownership(
                org.id, TransferOwnershipDto(new_owner_id=non_owner.id), non_owner.id
            )
        
        # Test: Non-owner cannot deactivate
        with pytest.raises(PermissionError):
             organization_use_cases.deactivate_organization(org.id, non_owner.id)
    
    @pytest.mark.io
     def test_organization_search_and_retrieval(self, organization_use_cases, sample_owner):
        """Test organization search and retrieval operations."""
        # Create organizations with distinct names
        org1 =  organization_use_cases.create_organization(
            sample_owner.id, CreateOrganizationDto(name="Search Test Org 1")
        )
        org2 =  organization_use_cases.create_organization(
            sample_owner.id, CreateOrganizationDto(name="Search Test Org 2")
        )
        
        # Test: Get by ID
        retrieved_org1 =  organization_use_cases.get_organization_by_id(org1.id)
        assert retrieved_org1 is not None
        assert retrieved_org1.name == "Search Test Org 1"
        
        # Test: Get by name
        retrieved_org2 =  organization_use_cases.get_organization_by_name("Search Test Org 2")
        assert retrieved_org2 is not None
        assert retrieved_org2.id == org2.id
        
        # Test: Get non-existent
        non_existent =  organization_use_cases.get_organization_by_id(uuid4())
        assert non_existent is None
        
        non_existent_name =  organization_use_cases.get_organization_by_name("Non Existent Org")
        assert non_existent_name is None
    
    @pytest.mark.io
     def test_concurrent_organization_operations(self, organization_use_cases, unit_of_work):
        """Test concurrent operations on organizations."""
        # Create owner and organization
         with unit_of_work:
            owner =  unit_of_work.users.create(
                UserFactory.create_user(email="concurrent@example.com")
            )
        
        org =  organization_use_cases.create_organization(
            owner.id, CreateOrganizationDto(name="Concurrent Test Org")
        )
        
        # Simulate concurrent updates (in real scenario these would be separate transactions)
        update1_dto = UpdateOrganizationDto(name="Concurrent Update 1")
        update2_dto = UpdateOrganizationDto(description="Concurrent Description Update")
        
        # Both updates should succeed when done sequentially
        result1 =  organization_use_cases.update_organization(org.id, update1_dto, owner.id)
        result2 =  organization_use_cases.update_organization(org.id, update2_dto, owner.id)
        
        assert result1.name == "Concurrent Update 1"
        assert result2.description == "Concurrent Description Update"
        assert result2.name == "Concurrent Update 1"  # Previous update preserved