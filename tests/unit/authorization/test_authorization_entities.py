from uuid import uuid4

from src.authorization.domain.entities.role import Role
from src.authorization.domain.entities.permission import Permission, PermissionAction
from src.authorization.domain.entities.policy import Policy, PolicyEffect


def test_create_role():
    role = Role.create(name="test_role", description="A test role", created_by=uuid4())
    assert isinstance(role, Role)
    assert role.name.value == "test_role"


def test_create_permission():
    permission = Permission.create(
        name="test_permission",
        description="A test permission",
        action=PermissionAction.READ,
        resource_type="test_resource",
    )
    assert isinstance(permission, Permission)
    assert permission.name.value == "test_permission"


def test_create_policy():
    policy = Policy.create(
        name="test_policy",
        description="A test policy",
        effect=PolicyEffect.ALLOW,
        resource_type="test_resource",
        action="read",
        conditions=[],
        created_by=uuid4(),
    )
    assert isinstance(policy, Policy)
    assert policy.name == "test_policy"
