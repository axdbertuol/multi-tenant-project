"""Integration tests for Organization entity with repository."""

import pytest
from uuid import uuid4

from src.iam.domain.entities.organization import Organization
from src.iam.infrastructure.repositories.sqlalchemy_organization_repository import SqlAlchemyOrganizationRepository
from src.iam.infrastructure.database.models import OrganizationModel


class TestOrganizationRepositoryIntegration:
    """Test Organization entity integration with SqlAlchemy repository."""

    def test_organization_save_and_retrieve_full_cycle(self, db_session):
        """Test full save and retrieve cycle with all new fields."""
        # Create repository
        repo = SqlAlchemyOrganizationRepository(db_session)
        
        # Create organization entity
        user_id = uuid4()
        org = Organization.create(
            name="Integration Test Org",
            owner_id=user_id,
            description="Test Description",
            max_users=25,
            max_members=50
        )
        
        # Save to database
        saved_org = repo.save(org)
        db_session.commit()
        
        # Verify saved organization
        assert saved_org.id == org.id
        assert saved_org.name.value == "Integration Test Org"
        assert saved_org.owner_id == user_id
        assert saved_org.member_count == 1
        assert saved_org.max_members == 50
        assert saved_org.settings.max_users == 25
        
        # Retrieve from database
        retrieved_org = repo.get_by_id(org.id)
        assert retrieved_org is not None
        assert retrieved_org.id == org.id
        assert retrieved_org.name.value == "Integration Test Org"
        assert retrieved_org.member_count == 1
        assert retrieved_org.max_members == 50
        assert retrieved_org.settings.max_users == 25

    def test_organization_database_model_fields(self, db_session):
        """Test that all fields are properly saved to database model."""
        # Create and save organization
        repo = SqlAlchemyOrganizationRepository(db_session)
        user_id = uuid4()
        
        org = Organization.create(
            name="Model Test Org",
            owner_id=user_id,
            max_users=15,
            max_members=30
        )
        
        saved_org = repo.save(org)
        db_session.commit()
        
        # Query the database model directly
        org_model = db_session.query(OrganizationModel).filter_by(id=org.id).first()
        assert org_model is not None
        assert org_model.name == "Model Test Org"
        assert org_model.owner_id == user_id
        assert org_model.member_count == 1
        assert org_model.max_members == 30
        assert org_model.is_active is True
        
        # Verify settings are stored as JSON
        assert isinstance(org_model.settings, dict)
        assert org_model.settings["max_users"] == 15
        assert "features_enabled" in org_model.settings

    def test_organization_settings_serialization_roundtrip(self, db_session):
        """Test settings serialization/deserialization works correctly."""
        repo = SqlAlchemyOrganizationRepository(db_session)
        user_id = uuid4()
        
        # Create organization with custom settings
        org = Organization.create(
            name="Settings Test Org",
            owner_id=user_id,
            max_users=20
        )
        
        # Modify settings
        updated_settings = org.settings.enable_feature("custom_branding")
        updated_settings = updated_settings.update_custom_setting("theme", "dark")
        org_with_settings = org.update_settings(updated_settings)
        
        # Save and retrieve
        repo.save(org_with_settings)
        db_session.commit()
        
        retrieved_org = repo.get_by_id(org.id)
        assert retrieved_org is not None
        assert retrieved_org.settings.is_feature_enabled("custom_branding") is True
        assert retrieved_org.settings.get_custom_setting("theme") == "dark"
        assert retrieved_org.settings.max_users == 20

    def test_organization_update_with_new_fields(self, db_session):
        """Test updating organization with member_count and max_members."""
        repo = SqlAlchemyOrganizationRepository(db_session)
        user_id = uuid4()
        
        # Create and save initial organization
        org = Organization.create("Update Test Org", user_id)
        repo.save(org)
        db_session.commit()
        
        # Update member count and max_members
        updated_org = org.update_member_count(5).update_max_members(100)
        repo.save(updated_org)
        db_session.commit()
        
        # Retrieve and verify
        retrieved_org = repo.get_by_id(org.id)
        assert retrieved_org.member_count == 5
        assert retrieved_org.max_members == 100

    def test_organization_validation_with_repository(self, db_session):
        """Test organization validation works with repository data."""
        repo = SqlAlchemyOrganizationRepository(db_session)
        user_id = uuid4()
        
        # Create organization with limits
        org = Organization.create(
            name="Validation Test Org",
            owner_id=user_id,
            max_users=10,
            max_members=5
        )
        
        repo.save(org)
        db_session.commit()
        
        # Test validation methods
        assert org.can_add_users(target_count=3) is True
        assert org.can_add_users(target_count=6) is False  # Exceeds max_members
        
        valid, msg = org.validate_user_limit(4)
        assert valid is True
        
        invalid, msg = org.validate_user_limit(6)
        assert invalid is False
        assert "maximum members limit" in msg