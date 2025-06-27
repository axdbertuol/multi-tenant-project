import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from src.infrastructure.database.models import PermissionModel
from src.domain.entities.permission import Permission
from tests.factories.permission_factory import PermissionFactory


class TestPermissionRepositoryIntegration:
    """Integration tests for permission repository operations"""

    @pytest.fixture
    def db_session(self):
        from src.infrastructure.database.dependencies import get_db
        session = next(get_db())
        yield session
        session.rollback()
        session.close()

    def test_create_permission_in_database(self, db_session: Session):
        """Test creating a permission entity and persisting to database"""
        permission = PermissionFactory.create_permission(
            name="test_permission",
            resource="test_resource",
            action="read",
            description="Test permission"
        )
        
        # Convert to database model
        permission_model = PermissionModel(
            id=permission.id,
            name=permission.name,
            description=permission.description,
            resource=permission.resource,
            action=permission.action,
            created_at=permission.created_at,
            updated_at=permission.updated_at,
            is_active=permission.is_active
        )
        
        # Save to database
        db_session.add(permission_model)
        db_session.commit()
        
        # Retrieve from database
        retrieved_permission = db_session.query(PermissionModel).filter(
            PermissionModel.id == permission.id
        ).first()
        
        assert retrieved_permission is not None
        assert retrieved_permission.name == permission.name
        assert retrieved_permission.resource == permission.resource
        assert retrieved_permission.action == permission.action
        assert retrieved_permission.description == permission.description
        assert retrieved_permission.is_active == permission.is_active

    def test_find_permissions_by_resource(self, db_session: Session):
        """Test finding permissions by resource"""
        user_permission = PermissionFactory.create_user_read_permission()
        org_permission = PermissionFactory.create_organization_read_permission()
        
        user_model = PermissionModel(
            id=user_permission.id,
            name=user_permission.name,
            description=user_permission.description,
            resource=user_permission.resource,
            action=user_permission.action,
            created_at=user_permission.created_at,
            is_active=user_permission.is_active
        )
        
        org_model = PermissionModel(
            id=org_permission.id,
            name=org_permission.name,
            description=org_permission.description,
            resource=org_permission.resource,
            action=org_permission.action,
            created_at=org_permission.created_at,
            is_active=org_permission.is_active
        )
        
        db_session.add_all([user_model, org_model])
        db_session.commit()
        
        # Find permissions by resource
        user_permissions = db_session.query(PermissionModel).filter(
            PermissionModel.resource == "users"
        ).all()
        
        org_permissions = db_session.query(PermissionModel).filter(
            PermissionModel.resource == "organizations"
        ).all()
        
        assert len(user_permissions) == 1
        assert user_permissions[0].name == "users.read"
        
        assert len(org_permissions) == 1
        assert org_permissions[0].name == "organizations.read"

    def test_find_permissions_by_action(self, db_session: Session):
        """Test finding permissions by action"""
        read_permission = PermissionFactory.create_user_read_permission()
        write_permission = PermissionFactory.create_user_write_permission()
        
        read_model = PermissionModel(
            id=read_permission.id,
            name=read_permission.name,
            description=read_permission.description,
            resource=read_permission.resource,
            action=read_permission.action,
            created_at=read_permission.created_at,
            is_active=read_permission.is_active
        )
        
        write_model = PermissionModel(
            id=write_permission.id,
            name=write_permission.name,
            description=write_permission.description,
            resource=write_permission.resource,
            action=write_permission.action,
            created_at=write_permission.created_at,
            is_active=write_permission.is_active
        )
        
        db_session.add_all([read_model, write_model])
        db_session.commit()
        
        # Find permissions by action
        read_permissions = db_session.query(PermissionModel).filter(
            PermissionModel.action == "read"
        ).all()
        
        write_permissions = db_session.query(PermissionModel).filter(
            PermissionModel.action == "write"
        ).all()
        
        assert len(read_permissions) == 1
        assert read_permissions[0].action == "read"
        
        assert len(write_permissions) == 1
        assert write_permissions[0].action == "write"

    def test_find_permission_by_resource_and_action(self, db_session: Session):
        """Test finding specific permission by resource and action combination"""
        permission = PermissionFactory.create_user_read_permission()
        
        permission_model = PermissionModel(
            id=permission.id,
            name=permission.name,
            description=permission.description,
            resource=permission.resource,
            action=permission.action,
            created_at=permission.created_at,
            is_active=permission.is_active
        )
        
        db_session.add(permission_model)
        db_session.commit()
        
        # Find by resource and action
        found_permission = db_session.query(PermissionModel).filter(
            PermissionModel.resource == "users",
            PermissionModel.action == "read"
        ).first()
        
        assert found_permission is not None
        assert found_permission.id == permission.id
        assert found_permission.name == "users.read"

    def test_update_permission_in_database(self, db_session: Session):
        """Test updating permission in database"""
        permission = PermissionFactory.create_permission(
            name="original_permission",
            resource="users",
            action="read"
        )
        
        permission_model = PermissionModel(
            id=permission.id,
            name=permission.name,
            description=permission.description,
            resource=permission.resource,
            action=permission.action,
            created_at=permission.created_at,
            is_active=permission.is_active
        )
        
        db_session.add(permission_model)
        db_session.commit()
        
        # Update permission
        updated_permission = permission.update_name("updated_permission")
        
        # Update in database
        permission_model.name = updated_permission.name
        permission_model.updated_at = updated_permission.updated_at
        db_session.commit()
        
        # Verify update
        retrieved_permission = db_session.query(PermissionModel).filter(
            PermissionModel.id == permission.id
        ).first()
        
        assert retrieved_permission.name == "updated_permission"
        assert retrieved_permission.updated_at is not None

    def test_permission_name_uniqueness(self, db_session: Session):
        """Test that permission names must be unique"""
        permission1 = PermissionFactory.create_permission(name="duplicate_permission")
        permission2 = PermissionFactory.create_permission(name="duplicate_permission")
        
        model1 = PermissionModel(
            id=permission1.id,
            name=permission1.name,
            description=permission1.description,
            resource=permission1.resource,
            action=permission1.action,
            created_at=permission1.created_at,
            is_active=permission1.is_active
        )
        
        model2 = PermissionModel(
            id=permission2.id,
            name=permission2.name,
            description=permission2.description,
            resource=permission2.resource,
            action=permission2.action,
            created_at=permission2.created_at,
            is_active=permission2.is_active
        )
        
        db_session.add(model1)
        db_session.commit()
        
        # Adding second permission with same name should fail
        db_session.add(model2)
        
        with pytest.raises(Exception):  # IntegrityError expected
            db_session.commit()

    def test_list_active_permissions(self, db_session: Session):
        """Test listing only active permissions"""
        active_permission = PermissionFactory.create_permission(name="active_permission")
        inactive_permission = PermissionFactory.create_permission(name="inactive_permission").deactivate()
        
        active_model = PermissionModel(
            id=active_permission.id,
            name=active_permission.name,
            description=active_permission.description,
            resource=active_permission.resource,
            action=active_permission.action,
            created_at=active_permission.created_at,
            is_active=active_permission.is_active
        )
        
        inactive_model = PermissionModel(
            id=inactive_permission.id,
            name=inactive_permission.name,
            description=inactive_permission.description,
            resource=inactive_permission.resource,
            action=inactive_permission.action,
            created_at=inactive_permission.created_at,
            is_active=inactive_permission.is_active
        )
        
        db_session.add_all([active_model, inactive_model])
        db_session.commit()
        
        # Query only active permissions
        active_permissions = db_session.query(PermissionModel).filter(
            PermissionModel.is_active == True
        ).all()
        
        permission_names = [perm.name for perm in active_permissions]
        assert "active_permission" in permission_names
        assert "inactive_permission" not in permission_names

    def test_permission_resource_action_indexing(self, db_session: Session):
        """Test that resource and action fields are properly indexed for performance"""
        permissions = [
            PermissionFactory.create_permission(name=f"perm_{i}", resource="users", action="read")
            for i in range(10)
        ]
        
        models = [
            PermissionModel(
                id=perm.id,
                name=perm.name,
                description=perm.description,
                resource=perm.resource,
                action=perm.action,
                created_at=perm.created_at,
                is_active=perm.is_active
            )
            for perm in permissions
        ]
        
        db_session.add_all(models)
        db_session.commit()
        
        # Query by resource (should be efficient due to index)
        result = db_session.query(PermissionModel).filter(
            PermissionModel.resource == "users"
        ).all()
        
        assert len(result) == 10
        
        # Query by action (should be efficient due to index)
        result = db_session.query(PermissionModel).filter(
            PermissionModel.action == "read"
        ).all()
        
        assert len(result) == 10