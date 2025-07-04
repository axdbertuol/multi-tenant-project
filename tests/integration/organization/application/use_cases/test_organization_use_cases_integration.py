import pytest
from uuid import uuid4
from src.iam.application.use_cases.organization_use_cases import OrganizationUseCases
from src.iam.application.dtos.organization_dto import (
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
            return unit_of_work.users.create(user)
    
    @pytest.fixture
    def sample_user(self, unit_of_work):
        """Create a sample user for testing memberships."""
        user = UserFactory.create_user(email="member@example.com")
        with unit_of_work:
            return unit_of_work.users.create(user)
    
    @pytest.mark.io
    def test_create_organization_full_flow(self, organization_use_cases, sample_owner):
        """Test complete organization creation flow."""
        # Arrange
        create_dto = CreateOrganizationDto(
            name="Integration Test Org",
            description="Test organization for integration testing"
        )
        
        # Act
        result = organization_use_cases.create_organization(sample_owner.id, create_dto)
        
        # Assert
        assert result is not None
        assert result.name == "Integration Test Org"
        assert result.description == "Test organization for integration testing"
        assert result.owner_id == sample_owner.id
        assert result.is_active is True
        
        # Verify owner is automatically added as member
        member_orgs = organization_use_cases.get_user_organizations(sample_owner.id)
        assert len(member_orgs) == 1
        assert member_orgs[0].id == result.id