from uuid import uuid4
from src.domain.entities.role import Role


class RoleFactory:
    @staticmethod
    def create_role(
        name: str = "test_role",
        description: str = None,
        is_system: bool = False
    ) -> Role:
        return Role.create(
            name=name,
            description=description,
            is_system=is_system
        )

    @staticmethod
    def create_admin_role() -> Role:
        return Role.create(
            name="admin",
            description="Administrator role with full access",
            is_system=True
        )

    @staticmethod
    def create_member_role() -> Role:
        return Role.create(
            name="member",
            description="Regular member role",
            is_system=False
        )

    @staticmethod
    def create_viewer_role() -> Role:
        return Role.create(
            name="viewer",
            description="Read-only viewer role",
            is_system=False
        )