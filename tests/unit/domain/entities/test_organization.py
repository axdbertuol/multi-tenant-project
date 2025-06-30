import pytest
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import ValidationError
from organization.domain.entities.organization import Organization


class TestOrganization:
    """Unit tests for Organization domain entity."""

    def test_create_organization(self):
        """Test creating a new organization."""
        owner_id = uuid4()
        org = Organization.create(
            name="Test Org",
            owner_id=owner_id,
            description="Test organization description",
        )

        assert isinstance(org.id, UUID)
        assert org.name.value == "Test Org"
        assert org.description == "Test organization description"
        assert org.owner_id == owner_id
        assert isinstance(org.created_at, datetime)
        assert org.updated_at is None
        assert org.is_active is True

    def test_create_organization_without_description(self):
        """Test creating an organization without description."""
        owner_id = uuid4()
        org = Organization.create(name="Test Org", owner_id=owner_id)

        assert org.name.value == "Test Org"
        assert org.description is None
        assert org.owner_id == owner_id
        assert org.is_active is True

    def test_organization_immutability(self):
        """Test that organization entity is immutable."""
        owner_id = uuid4()
        org = Organization.create(
            name="Test Org", owner_id=owner_id, description="Test description"
        )

        # Should not be able to directly modify attributes
        with pytest.raises(ValidationError):
            org.name.value = "New Name"

        with pytest.raises(ValidationError):
            org.owner_id = uuid4()

    def test_update_name(self):
        """Test updating organization name."""
        owner_id = uuid4()
        org = Organization.create(
            name="Test Org", owner_id=owner_id, description="Test description"
        )

        updated_org = org.update_name("Updated Org")

        # Original organization unchanged
        assert org.name.value == "Test Org"
        assert org.updated_at is None

        # New organization object with changes
        assert updated_org.name.value == "Updated Org"
        assert updated_org.updated_at is not None
        assert updated_org.id == org.id
        assert updated_org.owner_id == org.owner_id
        assert updated_org.description == org.description

    def test_update_description(self):
        """Test updating organization description."""
        owner_id = uuid4()
        org = Organization.create(
            name="Test Org", owner_id=owner_id, description="Original description"
        )

        updated_org = org.update_description("Updated description")

        # Original organization unchanged
        assert org.description == "Original description"
        assert org.updated_at is None

        # New organization object with changes
        assert updated_org.description == "Updated description"
        assert updated_org.updated_at is not None
        assert updated_org.id == org.id
        assert updated_org.name == org.name

    def test_transfer_ownership(self):
        """Test transferring organization ownership."""
        original_owner_id = uuid4()
        new_owner_id = uuid4()

        org = Organization.create(
            name="Test Org", owner_id=original_owner_id, description="Test description"
        )

        transferred_org = org.transfer_ownership(new_owner_id)

        # Original organization unchanged
        assert org.owner_id == original_owner_id
        assert org.updated_at is None

        # New organization object with changes
        assert transferred_org.owner_id == new_owner_id
        assert transferred_org.updated_at is not None
        assert transferred_org.id == org.id
        assert transferred_org.name == org.name

    def test_deactivate_organization(self):
        """Test deactivating an organization."""
        owner_id = uuid4()
        org = Organization.create(
            name="Test Org", owner_id=owner_id, description="Test description"
        )

        deactivated_org = org.deactivate()

        # Original organization unchanged
        assert org.is_active is True
        assert org.updated_at is None

        # New organization object with changes
        assert deactivated_org.is_active is False
        assert deactivated_org.updated_at is not None
        assert deactivated_org.id == org.id

    def test_activate_organization(self):
        """Test activating an organization."""
        owner_id = uuid4()
        org = Organization.create(
            name="Test Org", owner_id=owner_id, description="Test description"
        )

        # First deactivate
        deactivated_org = org.deactivate()

        # Then activate
        activated_org = deactivated_org.activate()

        assert activated_org.is_active is True
        assert activated_org.updated_at is not None
        assert activated_org.id == org.id

    def test_organization_creation_timestamps(self):
        """Test organization creation timestamps."""
        owner_id = uuid4()
        before_creation = datetime.utcnow()

        org = Organization.create(
            name="Test Org", owner_id=owner_id, description="Test description"
        )

        after_creation = datetime.utcnow()

        assert before_creation <= org.created_at <= after_creation
        assert org.updated_at is None

    def test_organization_update_timestamps(self):
        """Test organization update timestamps."""
        owner_id = uuid4()
        org = Organization.create(
            name="Test Org", owner_id=owner_id, description="Test description"
        )

        # Wait a bit to ensure different timestamp
        import time

        time.sleep(0.001)

        before_update = datetime.utcnow()
        updated_org = org.update_name("New Name")
        after_update = datetime.utcnow()

        assert before_update <= updated_org.updated_at <= after_update
        assert updated_org.created_at == org.created_at

    def test_organization_equality(self):
        """Test organization equality based on ID."""
        owner_id1 = uuid4()
        owner_id2 = uuid4()

        org1 = Organization.create(
            name="Org 1", owner_id=owner_id1, description="Description 1"
        )

        org2 = Organization.create(
            name="Org 2", owner_id=owner_id2, description="Description 2"
        )

        # Different organizations should not be equal
        assert org1 != org2

        # Same organization with modifications should still be equal (same ID)
        updated_org1 = org1.update_name("Updated Name")
        assert org1.id == updated_org1.id

    def test_organization_with_empty_name(self):
        """Test creating organization with empty name."""
        owner_id = uuid4()

        # This should work as name validation is handled at DTO level
        with pytest.raises(ValueError):
            org = Organization.create(
                name="", owner_id=owner_id, description="Test description"
            )
            assert org.name.value == ""

    def test_organization_string_representation(self):
        """Test organization string representation."""
        owner_id = uuid4()
        org = Organization.create(
            name="Test Org", owner_id=owner_id, description="Test description"
        )

        org_str = str(org)
        assert "Test Org" in org_str or str(org.id) in org_str

    def test_multiple_updates_preserve_creation_time(self):
        """Test that multiple updates preserve the original creation time."""
        owner_id = uuid4()
        org = Organization.create(
            name="Test Org", owner_id=owner_id, description="Original description"
        )

        original_created_at = org.created_at

        # Multiple updates
        updated_org1 = org.update_name("Updated Name")
        updated_org2 = updated_org1.update_description("Updated Description")
        new_owner_id = uuid4()
        updated_org3 = updated_org2.transfer_ownership(new_owner_id)

        # Creation time should remain the same
        assert updated_org3.created_at == original_created_at

        # But updated_at should be set
        assert updated_org3.updated_at is not None

    def test_organization_with_none_description(self):
        """Test creating organization with None description."""
        owner_id = uuid4()
        org = Organization.create(name="Test Org", owner_id=owner_id, description=None)

        assert org.description is None

        # Test updating to None
        updated_org = org.update_description(None)
        assert updated_org.description is None
        assert updated_org.updated_at is not None
