import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from src.infrastructure.database.models import RoleModel
from src.domain.entities.role import Role
from tests.factories.role_factory import RoleFactory


class TestRoleRepositoryIntegration:
    """Integration tests for role repository operations"""

    @pytest.fixture
    def db_session(self):
        from src.infrastructure.database.dependencies import get_db
        session = next(get_db())
        yield session
        session.rollback()
        session.close()

    def test_create_role_in_database(self, db_session: Session):
        """Test creating a role entity and persisting to database"""
        role = RoleFactory.create_role(
            name="test_integration_role",
            description="Integration test role"
        )
        
        # Convert to database model
        role_model = RoleModel(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            created_at=role.created_at,
            updated_at=role.updated_at,
            is_active=role.is_active
        )
        
        # Save to database
        db_session.add(role_model)
        db_session.commit()
        
        # Retrieve from database
        retrieved_role = db_session.query(RoleModel).filter(
            RoleModel.id == role.id
        ).first()
        
        assert retrieved_role is not None
        assert retrieved_role.name == role.name
        assert retrieved_role.description == role.description
        assert retrieved_role.is_system == role.is_system
        assert retrieved_role.is_active == role.is_active

    def test_find_role_by_name(self, db_session: Session):
        """Test finding role by name"""
        role = RoleFactory.create_role(name="unique_role_name")
        
        role_model = RoleModel(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            created_at=role.created_at,
            is_active=role.is_active
        )
        
        db_session.add(role_model)
        db_session.commit()
        
        # Find by name
        found_role = db_session.query(RoleModel).filter(
            RoleModel.name == "unique_role_name"
        ).first()
        
        assert found_role is not None
        assert found_role.id == role.id
        assert found_role.name == role.name

    def test_update_role_in_database(self, db_session: Session):
        """Test updating role in database"""
        role = RoleFactory.create_role(name="original_name")
        
        role_model = RoleModel(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            created_at=role.created_at,
            is_active=role.is_active
        )
        
        db_session.add(role_model)
        db_session.commit()
        
        # Update role
        updated_role = role.update_name("updated_name")
        
        # Update in database
        role_model.name = updated_role.name
        role_model.updated_at = updated_role.updated_at
        db_session.commit()
        
        # Verify update
        retrieved_role = db_session.query(RoleModel).filter(
            RoleModel.id == role.id
        ).first()
        
        assert retrieved_role.name == "updated_name"
        assert retrieved_role.updated_at is not None

    def test_deactivate_role_in_database(self, db_session: Session):
        """Test deactivating role in database"""
        role = RoleFactory.create_role()
        
        role_model = RoleModel(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            created_at=role.created_at,
            is_active=role.is_active
        )
        
        db_session.add(role_model)
        db_session.commit()
        
        # Deactivate role
        deactivated_role = role.deactivate()
        
        # Update in database
        role_model.is_active = deactivated_role.is_active
        role_model.updated_at = deactivated_role.updated_at
        db_session.commit()
        
        # Verify deactivation
        retrieved_role = db_session.query(RoleModel).filter(
            RoleModel.id == role.id
        ).first()
        
        assert retrieved_role.is_active is False
        assert retrieved_role.updated_at is not None

    def test_system_role_integrity(self, db_session: Session):
        """Test system role creation and constraints"""
        system_role = RoleFactory.create_admin_role()
        
        role_model = RoleModel(
            id=system_role.id,
            name=system_role.name,
            description=system_role.description,
            is_system=system_role.is_system,
            created_at=system_role.created_at,
            is_active=system_role.is_active
        )
        
        db_session.add(role_model)
        db_session.commit()
        
        # Verify system role properties
        retrieved_role = db_session.query(RoleModel).filter(
            RoleModel.id == system_role.id
        ).first()
        
        assert retrieved_role.is_system is True
        assert retrieved_role.name == "admin"

    def test_role_name_uniqueness(self, db_session: Session):
        """Test that role names must be unique"""
        role1 = RoleFactory.create_role(name="duplicate_name")
        role2 = RoleFactory.create_role(name="duplicate_name")
        
        role_model1 = RoleModel(
            id=role1.id,
            name=role1.name,
            description=role1.description,
            is_system=role1.is_system,
            created_at=role1.created_at,
            is_active=role1.is_active
        )
        
        role_model2 = RoleModel(
            id=role2.id,
            name=role2.name,
            description=role2.description,
            is_system=role2.is_system,
            created_at=role2.created_at,
            is_active=role2.is_active
        )
        
        db_session.add(role_model1)
        db_session.commit()
        
        # Adding second role with same name should fail
        db_session.add(role_model2)
        
        with pytest.raises(Exception):  # IntegrityError expected
            db_session.commit()

    def test_list_active_roles(self, db_session: Session):
        """Test listing only active roles"""
        active_role = RoleFactory.create_role(name="active_role")
        inactive_role = RoleFactory.create_role(name="inactive_role").deactivate()
        
        active_model = RoleModel(
            id=active_role.id,
            name=active_role.name,
            description=active_role.description,
            is_system=active_role.is_system,
            created_at=active_role.created_at,
            is_active=active_role.is_active
        )
        
        inactive_model = RoleModel(
            id=inactive_role.id,
            name=inactive_role.name,
            description=inactive_role.description,
            is_system=inactive_role.is_system,
            created_at=inactive_role.created_at,
            is_active=inactive_role.is_active
        )
        
        db_session.add_all([active_model, inactive_model])
        db_session.commit()
        
        # Query only active roles
        active_roles = db_session.query(RoleModel).filter(
            RoleModel.is_active == True
        ).all()
        
        role_names = [role.name for role in active_roles]
        assert "active_role" in role_names
        assert "inactive_role" not in role_names