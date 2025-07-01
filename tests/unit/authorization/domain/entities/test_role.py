import pytest
from datetime import datetime
from uuid import uuid4

from authorization.domain.entities.role import Role

id = uuid4()


class TestRole:
    def test_create_role_with_minimal_data(self):
        role = Role.create(name="admin", description="asadasa", created_by=id)

        assert role.name.value == "admin"
        # assert role.description is None
        assert role.is_system_role is False
        assert role.is_active is True
        assert isinstance(role.id, type(uuid4()))
        assert isinstance(role.created_at, datetime)
        assert role.updated_at is None

    def test_create_role_with_all_data(self):
        role = Role.create(
            name="super_admin",
            description="Super administrator role",
            is_system_role=True,
            created_by=id,
        )

        assert role.name.value == "super_admin"
        assert role.description == "Super administrator role"
        assert role.is_system_role is True
        assert role.is_active is True

    def test_update_description(self):
        role = Role.create(
            name="super_admin",
            description="Super administrator role",
            is_system_role=True,
            created_by=id,
        )
        updated_role = role.update_description("New description")

        assert updated_role.description == "New description"
        assert updated_role.id == role.id
        assert isinstance(updated_role.updated_at, datetime)

    def test_deactivate_role(self):
        role = Role.create(
            name="super_admin",
            description="Super administrator role",
            created_by=id,
        )
        deactivated_role = role.deactivate()

        assert deactivated_role.is_active is False
        assert deactivated_role.id == role.id
        assert isinstance(deactivated_role.updated_at, datetime)

    def test_activate_role(self):
        role = Role.create(
            name="super_admin",
            description="Super administrator role",
            created_by=id,
        )
        deactivated_role = role.deactivate()
        activated_role = deactivated_role.activate()

        assert activated_role.is_active is True
        assert activated_role.id == role.id
        assert isinstance(activated_role.updated_at, datetime)

    def test_role_immutability(self):
        role = Role.create(
            name="super_admin",
            description="Super administrator role",
            created_by=id,
        )

        with pytest.raises(Exception):
            role.name.value = "new_name"
