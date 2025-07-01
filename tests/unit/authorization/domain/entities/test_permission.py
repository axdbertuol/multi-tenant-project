import pytest
from datetime import datetime
from uuid import uuid4

from src.authorization.domain.entities.permission import Permission, PermissionAction


class TestPermission:
    def test_create_permission_with_minimal_data(self):
        permission = Permission.create(
            name="read_users", 
            resource_type="user", 
            action=PermissionAction.READ,
            description="Read users permission"
        )

        assert permission.name.value == "read_users"
        assert permission.resource_type == "user"
        assert permission.action == PermissionAction.READ
        assert permission.description == "Read users permission"
        assert permission.is_active is True
        assert isinstance(permission.id, type(uuid4()))
        assert isinstance(permission.created_at, datetime)
        assert permission.updated_at is None

    def test_create_permission_with_all_data(self):
        permission = Permission.create(
            name="write_posts",
            resource_type="post",
            action=PermissionAction.UPDATE,
            description="Allow writing posts"
        )

        assert permission.name.value == "write_posts"
        assert permission.resource_type == "post"
        assert permission.action == PermissionAction.UPDATE
        assert permission.description == "Allow writing posts"
        assert permission.is_active is True

    def test_update_description(self):
        permission = Permission.create(
            name="read_users", 
            resource_type="user", 
            action=PermissionAction.READ,
            description="Original description"
        )
        updated_permission = permission.update_description("New description")

        assert updated_permission.description == "New description"
        assert updated_permission.id == permission.id
        assert updated_permission.resource_type == "user"
        assert updated_permission.action == PermissionAction.READ
        assert isinstance(updated_permission.updated_at, datetime)
        assert updated_permission.updated_at != permission.updated_at

    def test_get_full_name(self):
        permission = Permission.create(
            name="read_users", 
            resource_type="user", 
            action=PermissionAction.READ,
            description="Read users permission"
        )
        
        full_name = permission.get_full_name()
        assert full_name == "user:read"

    def test_deactivate_permission(self):
        permission = Permission.create(
            name="read_users", 
            resource_type="user", 
            action=PermissionAction.READ,
            description="Read users permission"
        )
        deactivated_permission = permission.deactivate()

        assert deactivated_permission.is_active is False
        assert deactivated_permission.id == permission.id
        assert isinstance(deactivated_permission.updated_at, datetime)

    def test_activate_permission(self):
        permission = Permission.create(
            name="read_users", 
            resource_type="user", 
            action=PermissionAction.READ,
            description="Read users permission"
        )
        deactivated_permission = permission.deactivate()
        activated_permission = deactivated_permission.activate()

        assert activated_permission.is_active is True
        assert activated_permission.id == permission.id
        assert isinstance(activated_permission.updated_at, datetime)

    def test_permission_immutability(self):
        permission = Permission.create(
            name="read_users", 
            resource_type="user", 
            action=PermissionAction.READ,
            description="Read users permission"
        )

        with pytest.raises(Exception):
            permission.name = "new_name"
    
    def test_matches_resource_and_action(self):
        permission = Permission.create(
            name="read_users", 
            resource_type="user", 
            action=PermissionAction.READ,
            description="Read users permission"
        )
        
        assert permission.matches_resource_and_action("user", PermissionAction.READ) is True
        assert permission.matches_resource_and_action("user", PermissionAction.UPDATE) is False
        assert permission.matches_resource_and_action("post", PermissionAction.READ) is False
    
    def test_system_permission_cannot_be_deactivated(self):
        permission = Permission.create(
            name="system_permission", 
            resource_type="system", 
            action=PermissionAction.MANAGE,
            description="System permission",
            is_system_permission=True
        )
        
        with pytest.raises(ValueError, match="Cannot deactivate system permissions"):
            permission.deactivate()
    
    def test_can_be_deleted_system_permission(self):
        permission = Permission.create(
            name="system_permission", 
            resource_type="system", 
            action=PermissionAction.MANAGE,
            description="System permission",
            is_system_permission=True
        )
        
        can_delete, reason = permission.can_be_deleted()
        assert can_delete is False
        assert reason == "System permissions cannot be deleted"
    
    def test_can_be_deleted_regular_permission(self):
        permission = Permission.create(
            name="regular_permission", 
            resource_type="user", 
            action=PermissionAction.READ,
            description="Regular permission"
        )
        
        can_delete, reason = permission.can_be_deleted()
        assert can_delete is True
        assert reason == "Permission can be deleted"
