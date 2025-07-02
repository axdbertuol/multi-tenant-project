from uuid import uuid4
from src.authorization.domain.entities.permission import Permission, PermissionAction


class PermissionFactory:
    @staticmethod
    def create_permission(
        name: str = "test_permission",
        resource_type: str = "test_resource",
        action: PermissionAction = PermissionAction.READ,
        description: str = "Test permission",
    ) -> Permission:
        return Permission.create(
            name=name,
            resource_type=resource_type,
            action=action,
            description=description,
        )

    @staticmethod
    def create_user_read_permission() -> Permission:
        return Permission.create(
            name="users.read",
            resource_type="user",
            action=PermissionAction.READ,
            description="Read users permission",
        )

    @staticmethod
    def create_user_write_permission() -> Permission:
        return Permission.create(
            name="users.update",
            resource_type="user",
            action=PermissionAction.UPDATE,
            description="Update users permission",
        )

    @staticmethod
    def create_user_delete_permission() -> Permission:
        return Permission.create(
            name="users.delete",
            resource_type="user",
            action=PermissionAction.DELETE,
            description="Delete users permission",
        )

    @staticmethod
    def create_organization_read_permission() -> Permission:
        return Permission.create(
            name="organizations.read",
            resource_type="organization",
            action=PermissionAction.READ,
            description="Read organizations permission",
        )

    @staticmethod
    def create_organization_write_permission() -> Permission:
        return Permission.create(
            name="organizations.update",
            resource_type="organization",
            action=PermissionAction.UPDATE,
            description="Update organizations permission",
        )
