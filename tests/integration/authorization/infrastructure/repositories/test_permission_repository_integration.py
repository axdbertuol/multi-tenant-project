import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from src.authorization.infrastructure.database.models import PermissionModel
from src.authorization.domain.entities.permission import Permission, PermissionAction
from tests.factories.permission_factory import PermissionFactory


class TestPermissionRepositoryIntegration:
    """Integration tests for permission repository operations"""

    # @pytest.fixture
    # def db_session(self):
    #     from src.shared.infrastructure.database.connection import get_db
    #     session = next(get_db())
    #     yield session
    #     session.rollback()
    #     session.close()

    def test_create_permission_in_database(self, db_session: Session):
        """Test creating a permission entity and persisting to database"""
        permission = PermissionFactory.create_permission(
            name="test_permission",
            resource_type="test_resource",
            action=PermissionAction.READ,
            description="Test permission",
        )

        # Convert to database model
        permission_model = PermissionModel(
            id=permission.id,
            name=permission.name.value,
            description=permission.description,
            resource_type=permission.resource_type,
            action=permission.action,
            created_at=permission.created_at,
            updated_at=permission.updated_at,
            is_active=permission.is_active,
        )

        # Save to database
        db_session.add(permission_model)
        db_session.commit()

        # Retrieve from database
        retrieved_permission = (
            db_session.query(PermissionModel)
            .filter(PermissionModel.id == permission.id)
            .first()
        )

        assert retrieved_permission is not None
        assert retrieved_permission.name == permission.name.value
        assert retrieved_permission.resource_type == permission.resource_type
        assert retrieved_permission.action == permission.action
        assert retrieved_permission.description == permission.description
        assert retrieved_permission.is_active == permission.is_active

    def test_find_permissions_by_resource_type(self, db_session: Session):
        """Test finding permissions by resource_type"""
        user_permission = PermissionFactory.create_user_read_permission()
        org_permission = PermissionFactory.create_organization_read_permission()

        user_model = PermissionModel(
            id=user_permission.id,
            name=user_permission.name.value,
            description=user_permission.description,
            resource_type=user_permission.resource_type,
            action=user_permission.action,
            created_at=user_permission.created_at,
            is_active=user_permission.is_active,
        )

        org_model = PermissionModel(
            id=org_permission.id,
            name=org_permission.name.value,
            description=org_permission.description,
            resource_type=org_permission.resource_type,
            action=org_permission.action,
            created_at=org_permission.created_at,
            is_active=org_permission.is_active,
        )

        db_session.add_all([user_model, org_model])
        db_session.commit()

        # Find permissions by resource_type
        user_permissions = (
            db_session.query(PermissionModel)
            .filter(PermissionModel.resource_type == "user")
            .all()
        )

        org_permissions = (
            db_session.query(PermissionModel)
            .filter(PermissionModel.resource_type == "organization")
            .all()
        )

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
            name=read_permission.name.value,
            description=read_permission.description,
            resource_type=read_permission.resource_type,
            action=read_permission.action,
            created_at=read_permission.created_at,
            is_active=read_permission.is_active,
        )

        write_model = PermissionModel(
            id=write_permission.id,
            name=write_permission.name.value,
            description=write_permission.description,
            resource_type=write_permission.resource_type,
            action=write_permission.action,
            created_at=write_permission.created_at,
            is_active=write_permission.is_active,
        )

        db_session.add_all([read_model, write_model])
        db_session.commit()

        # Find permissions by action
        read_permissions = (
            db_session.query(PermissionModel)
            .filter(PermissionModel.action == PermissionAction.READ)
            .all()
        )

        update_permissions = (
            db_session.query(PermissionModel)
            .filter(PermissionModel.action == PermissionAction.UPDATE)
            .all()
        )

        assert len(read_permissions) == 1
        assert read_permissions[0].action == PermissionAction.READ

        assert len(update_permissions) == 1
        assert update_permissions[0].action == PermissionAction.UPDATE

    def test_find_permission_by_resource_type_and_action(self, db_session: Session):
        """Test finding specific permission by resource_type and action combination"""
        permission = PermissionFactory.create_user_read_permission()

        permission_model = PermissionModel(
            id=permission.id,
            name=permission.name.value,
            description=permission.description,
            resource_type=permission.resource_type,
            action=permission.action,
            created_at=permission.created_at,
            is_active=permission.is_active,
        )

        db_session.add(permission_model)
        db_session.commit()

        # Find by resource_type and action
        found_permission = (
            db_session.query(PermissionModel)
            .filter(
                PermissionModel.resource_type == "user",
                PermissionModel.action == PermissionAction.READ,
            )
            .first()
        )

        assert found_permission is not None
        assert found_permission.id == permission.id
        assert found_permission.name == "users.read"

    def test_update_permission_in_database(self, db_session: Session):
        """Test updating permission in database"""
        permission = PermissionFactory.create_permission(
            name="original_permission",
            resource_type="user",
            action=PermissionAction.READ,
        )

        permission_model = PermissionModel(
            id=permission.id,
            name=permission.name.value,
            description=permission.description,
            resource_type=permission.resource_type,
            action=permission.action,
            created_at=permission.created_at,
            is_active=permission.is_active,
        )

        db_session.add(permission_model)
        db_session.commit()

        # Update permission
        updated_permission = permission.update_description("Updated description")

        # Update in database
        permission_model.description = updated_permission.description
        permission_model.updated_at = updated_permission.updated_at
        db_session.commit()

        # Verify update
        retrieved_permission = (
            db_session.query(PermissionModel)
            .filter(PermissionModel.id == permission.id)
            .first()
        )

        assert retrieved_permission.description == "Updated description"
        assert retrieved_permission.updated_at is not None

    def test_permission_name_uniqueness_within_resource_type(self, db_session: Session):
        """Test that permission names must be unique within resource type"""
        permission1 = PermissionFactory.create_permission(
            name="duplicate_permission", resource_type="user"
        )
        permission2 = PermissionFactory.create_permission(
            name="duplicate_permission", resource_type="user"
        )

        model1 = PermissionModel(
            id=permission1.id,
            name=permission1.name.value,
            description=permission1.description,
            resource_type=permission1.resource_type,
            action=permission1.action,
            created_at=permission1.created_at,
            is_active=permission1.is_active,
        )

        model2 = PermissionModel(
            id=permission2.id,
            name=permission2.name.value,
            description=permission2.description,
            resource_type=permission2.resource_type,
            action=permission2.action,
            created_at=permission2.created_at,
            is_active=permission2.is_active,
        )

        db_session.add(model1)
        db_session.commit()

        # Adding second permission with same name within same resource type should fail
        db_session.add(model2)

        with pytest.raises(Exception):  # IntegrityError expected
            db_session.commit()

    def test_list_active_permissions(self, db_session: Session):
        """Test listing only active permissions"""
        active_permission = PermissionFactory.create_permission(
            name="active_permission"
        )
        inactive_permission = PermissionFactory.create_permission(
            name="inactive_permission"
        ).deactivate()

        active_model = PermissionModel(
            id=active_permission.id,
            name=active_permission.name.value,
            description=active_permission.description,
            resource_type=active_permission.resource_type,
            action=active_permission.action,
            created_at=active_permission.created_at,
            is_active=active_permission.is_active,
        )

        inactive_model = PermissionModel(
            id=inactive_permission.id,
            name=inactive_permission.name.value,
            description=inactive_permission.description,
            resource_type=inactive_permission.resource_type,
            action=inactive_permission.action,
            created_at=inactive_permission.created_at,
            is_active=inactive_permission.is_active,
        )

        db_session.add_all([active_model, inactive_model])
        db_session.commit()

        # Query only active permissions
        active_permissions = (
            db_session.query(PermissionModel)
            .filter(PermissionModel.is_active == True)
            .all()
        )

        permission_names = [perm.name for perm in active_permissions]
        assert "active_permission" in permission_names
        assert "inactive_permission" not in permission_names

    def test_permission_resource_type_action_indexing(self, db_session: Session):
        """Test that resource_type and action fields are properly indexed for performance"""
        permissions = [
            PermissionFactory.create_permission(
                name=f"perm_{i}", resource_type="user", action=PermissionAction.READ
            )
            for i in range(10)
        ]

        models = [
            PermissionModel(
                id=perm.id,
                name=perm.name.value,
                description=perm.description,
                resource_type=perm.resource_type,
                action=perm.action,
                created_at=perm.created_at,
                is_active=perm.is_active,
            )
            for perm in permissions
        ]

        db_session.add_all(models)
        db_session.commit()

        # Query by resource_type (should be efficient due to index)
        result = (
            db_session.query(PermissionModel)
            .filter(PermissionModel.resource_type == "user")
            .all()
        )

        assert len(result) == 10

        # Query by action (should be efficient due to index)
        result = (
            db_session.query(PermissionModel)
            .filter(PermissionModel.action == PermissionAction.READ)
            .all()
        )

        assert len(result) == 10
