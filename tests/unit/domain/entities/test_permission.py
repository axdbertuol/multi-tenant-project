import pytest
from datetime import datetime
from uuid import uuid4

from src.domain.entities.permission import Permission


class TestPermission:
    def test_create_permission_with_minimal_data(self):
        permission = Permission.create(
            name="read_users",
            resource="users",
            action="read"
        )
        
        assert permission.name == "read_users"
        assert permission.resource == "users"
        assert permission.action == "read"
        assert permission.description is None
        assert permission.is_active is True
        assert isinstance(permission.id, type(uuid4()))
        assert isinstance(permission.created_at, datetime)
        assert permission.updated_at is None

    def test_create_permission_with_all_data(self):
        permission = Permission.create(
            name="write_posts",
            resource="posts",
            action="write",
            description="Allow writing posts"
        )
        
        assert permission.name == "write_posts"
        assert permission.resource == "posts"
        assert permission.action == "write"
        assert permission.description == "Allow writing posts"
        assert permission.is_active is True

    def test_update_name(self):
        permission = Permission.create(
            name="read_users",
            resource="users", 
            action="read"
        )
        updated_permission = permission.update_name("view_users")
        
        assert updated_permission.name == "view_users"
        assert updated_permission.id == permission.id
        assert updated_permission.resource == "users"
        assert updated_permission.action == "read"
        assert isinstance(updated_permission.updated_at, datetime)
        assert updated_permission.updated_at != permission.updated_at

    def test_update_description(self):
        permission = Permission.create(
            name="read_users",
            resource="users",
            action="read"
        )
        updated_permission = permission.update_description("New description")
        
        assert updated_permission.description == "New description"
        assert updated_permission.id == permission.id
        assert isinstance(updated_permission.updated_at, datetime)

    def test_deactivate_permission(self):
        permission = Permission.create(
            name="read_users",
            resource="users",
            action="read"
        )
        deactivated_permission = permission.deactivate()
        
        assert deactivated_permission.is_active is False
        assert deactivated_permission.id == permission.id
        assert isinstance(deactivated_permission.updated_at, datetime)

    def test_activate_permission(self):
        permission = Permission.create(
            name="read_users",
            resource="users",
            action="read"
        )
        deactivated_permission = permission.deactivate()
        activated_permission = deactivated_permission.activate()
        
        assert activated_permission.is_active is True
        assert activated_permission.id == permission.id
        assert isinstance(activated_permission.updated_at, datetime)

    def test_permission_immutability(self):
        permission = Permission.create(
            name="read_users",
            resource="users",
            action="read"
        )
        
        with pytest.raises(Exception):
            permission.name = "new_name"