from uuid import uuid4
from src.domain.entities.permission import Permission


class PermissionFactory:
    @staticmethod
    def create_permission(
        name: str = "test_permission",
        resource: str = "test_resource",
        action: str = "read",
        description: str = None
    ) -> Permission:
        return Permission.create(
            name=name,
            resource=resource,
            action=action,
            description=description
        )

    @staticmethod
    def create_user_read_permission() -> Permission:
        return Permission.create(
            name="users.read",
            resource="users",
            action="read",
            description="Read users permission"
        )

    @staticmethod
    def create_user_write_permission() -> Permission:
        return Permission.create(
            name="users.write",
            resource="users",
            action="write",
            description="Write users permission"
        )

    @staticmethod
    def create_user_delete_permission() -> Permission:
        return Permission.create(
            name="users.delete",
            resource="users",
            action="delete",
            description="Delete users permission"
        )

    @staticmethod
    def create_organization_read_permission() -> Permission:
        return Permission.create(
            name="organizations.read",
            resource="organizations",
            action="read",
            description="Read organizations permission"
        )

    @staticmethod
    def create_organization_write_permission() -> Permission:
        return Permission.create(
            name="organizations.write",
            resource="organizations",
            action="write",
            description="Write organizations permission"
        )