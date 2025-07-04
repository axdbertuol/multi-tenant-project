"""Unit tests for Organization entity integration with repository."""

import pytest
from uuid import uuid4
from datetime import datetime

from src.iam.domain.entities.organization import Organization
from src.iam.domain.value_objects.organization_name import OrganizationName
from src.iam.domain.value_objects.organization_settings import OrganizationSettings


class TestOrganizationEntityIntegration:
    """Test Organization entity compatibility with database model."""

    def test_organization_creation_with_new_fields(self):
        """Test that organization entity creates with all required fields."""
        user_id = uuid4()
        
        # Test creation with default values
        org = Organization.create(
            name="Test Organization",
            owner_id=user_id,
            description="Test Description"
        )
        
        assert org.name.value == "Test Organization"
        assert org.owner_id == user_id
        assert org.description == "Test Description"
        assert org.member_count == 1  # Should default to 1 (owner)
        assert org.max_members is None  # Should default to None
        assert org.is_active is True
        assert isinstance(org.settings, OrganizationSettings)

    def test_organization_creation_with_max_members(self):
        """Test organization creation with max_members specified."""
        user_id = uuid4()
        
        org = Organization.create(
            name="Test Organization",
            owner_id=user_id,
            max_members=100
        )
        
        assert org.member_count == 1
        assert org.max_members == 100

    def test_member_count_management(self):
        """Test member count management methods."""
        user_id = uuid4()
        org = Organization.create("Test Org", user_id)
        
        # Test increment
        updated_org = org.increment_member_count()
        assert updated_org.member_count == 2
        assert updated_org.updated_at is not None
        
        # Test decrement
        decremented_org = updated_org.decrement_member_count()
        assert decremented_org.member_count == 1
        
        # Test manual update
        manual_org = org.update_member_count(5)
        assert manual_org.member_count == 5

    def test_max_members_management(self):
        """Test max_members management."""
        user_id = uuid4()
        org = Organization.create("Test Org", user_id)
        
        # Update max_members
        updated_org = org.update_max_members(50)
        assert updated_org.max_members == 50
        assert updated_org.updated_at is not None

    def test_can_add_users_with_limits(self):
        """Test can_add_users method respects both limits."""
        user_id = uuid4()
        
        # Create org with settings max_users=5 and max_members=3
        org = Organization.create(
            name="Test Org",
            owner_id=user_id,
            max_users=5,
            max_members=3
        )
        
        # Should respect the lower limit (max_members=3)
        assert org.can_add_users(target_count=2) is True  # Within both limits
        assert org.can_add_users(target_count=3) is True  # At max_members limit
        assert org.can_add_users(target_count=4) is False  # Exceeds max_members
        assert org.can_add_users(target_count=6) is False  # Exceeds both limits

    def test_validation_methods(self):
        """Test validation methods."""
        user_id = uuid4()
        org = Organization.create(
            name="Test Org",
            owner_id=user_id,
            max_users=5,
            max_members=3
        )
        
        # Test user limit validation
        valid, msg = org.validate_user_limit(2)
        assert valid is True
        assert "validation passed" in msg
        
        invalid_settings, msg = org.validate_user_limit(6)
        assert invalid_settings is False
        assert "maximum user limit" in msg
        
        invalid_members, msg = org.validate_user_limit(4)
        assert invalid_members is False
        assert "maximum members limit" in msg
        
        # Test member count consistency
        valid, msg = org.validate_member_count_consistency()
        assert valid is True

    def test_organization_settings_serialization(self):
        """Test OrganizationSettings to_dict and from_dict methods."""
        # Create settings
        settings = OrganizationSettings.create_default(max_users=20)
        
        # Test to_dict
        settings_dict = settings.to_dict()
        assert isinstance(settings_dict, dict)
        assert settings_dict["max_users"] == 20
        assert "features_enabled" in settings_dict
        assert "custom_settings" in settings_dict
        
        # Test from_dict
        restored_settings = OrganizationSettings.from_dict(settings_dict)
        assert restored_settings.max_users == 20
        assert restored_settings.allow_user_registration == settings.allow_user_registration
        assert restored_settings.features_enabled == settings.features_enabled

    def test_organization_with_settings_serialization(self):
        """Test that organization works with settings serialization."""
        user_id = uuid4()
        org = Organization.create(
            name="Test Org",
            owner_id=user_id,
            max_users=15
        )
        
        # Verify settings can be serialized
        settings_dict = org.settings.to_dict()
        assert settings_dict["max_users"] == 15
        
        # Verify settings can be restored
        restored_settings = OrganizationSettings.from_dict(settings_dict)
        assert restored_settings.max_users == 15

    def test_model_dump_compatibility(self):
        """Test model_dump method for DTO compatibility."""
        settings = OrganizationSettings.create_default()
        
        # Test model_dump (alias for to_dict)
        dump = settings.model_dump()
        to_dict_result = settings.to_dict()
        
        assert dump == to_dict_result
        assert isinstance(dump, dict)

    def test_organization_immutability(self):
        """Test that organization entity is immutable."""
        user_id = uuid4()
        org = Organization.create("Test Org", user_id)
        
        # All updates should return new instances
        updated_name = org.update_name("New Name")
        assert org.name.value == "Test Org"  # Original unchanged
        assert updated_name.name.value == "New Name"  # New instance changed
        assert org.id == updated_name.id  # Same ID
        
        updated_count = org.increment_member_count()
        assert org.member_count == 1  # Original unchanged
        assert updated_count.member_count == 2  # New instance changed