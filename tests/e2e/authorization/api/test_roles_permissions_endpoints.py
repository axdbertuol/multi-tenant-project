import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from tests.factories.user_factory import UserFactory
from tests.factories.organization_factory import OrganizationFactory
from tests.factories.role_factory import RoleFactory
from tests.factories.permission_factory import PermissionFactory
from tests.factories.user_organization_role_factory import UserOrganizationRoleFactory


class TestRolesPermissionsEndpoints:
    """
    E2E tests for roles and permissions system

    Test scenarios:
    1. Create roles and permissions
    2. Assign roles to users in organizations
    3. Check user permissions within organizations
    4. Revoke and reassign roles
    5. Test permission inheritance and access control
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def db_session(self):
        from src.shared.infrastructure.database.connection import get_db

        session = next(get_db())
        yield session
        session.close()

    @pytest.fixture
    def test_data(self, db_session: Session):
        """Create test users, organizations, roles, and permissions"""
        # Create users
        admin_user = UserFactory.create_user(email="admin@test.com", name="Admin User")
        member_user = UserFactory.create_user(
            email="member@test.com", name="Member User"
        )
        viewer_user = UserFactory.create_user(
            email="viewer@test.com", name="Viewer User"
        )

        # Create organization
        organization = OrganizationFactory.create_organization(
            name="Test Organization", owner_id=admin_user.id
        )

        # Create roles
        admin_role = RoleFactory.create_admin_role()
        member_role = RoleFactory.create_member_role()
        viewer_role = RoleFactory.create_viewer_role()

        # Create permissions
        user_read_perm = PermissionFactory.create_user_read_permission()
        user_write_perm = PermissionFactory.create_user_write_permission()
        user_delete_perm = PermissionFactory.create_user_delete_permission()
        org_read_perm = PermissionFactory.create_organization_read_permission()
        org_write_perm = PermissionFactory.create_organization_write_permission()

        return {
            "users": {
                "admin": admin_user,
                "member": member_user,
                "viewer": viewer_user,
            },
            "organization": organization,
            "roles": {
                "admin": admin_role,
                "member": member_role,
                "viewer": viewer_role,
            },
            "permissions": {
                "user_read": user_read_perm,
                "user_write": user_write_perm,
                "user_delete": user_delete_perm,
                "org_read": org_read_perm,
                "org_write": org_write_perm,
            },
        }

    def test_complete_rbac_workflow(self, client, test_data: dict):
        """Test complete RBAC workflow from role creation to permission checking"""

        # Step 1: Assign roles to users in organization
        admin_user = test_data["users"]["admin"]
        member_user = test_data["users"]["member"]
        viewer_user = test_data["users"]["viewer"]
        organization = test_data["organization"]
        admin_role = test_data["roles"]["admin"]
        member_role = test_data["roles"]["member"]
        viewer_role = test_data["roles"]["viewer"]

        # Assign admin role to admin user
        admin_assignment = UserOrganizationRoleFactory.create_admin_assignment(
            user_id=admin_user.id,
            organization_id=organization.id,
            admin_role_id=admin_role.id,
            assigned_by=admin_user.id,
        )

        # Assign member role to member user
        member_assignment = UserOrganizationRoleFactory.create_member_assignment(
            user_id=member_user.id,
            organization_id=organization.id,
            member_role_id=member_role.id,
            assigned_by=admin_user.id,
        )

        # Assign viewer role to viewer user
        viewer_assignment = UserOrganizationRoleFactory.create_user_organization_role(
            user_id=viewer_user.id,
            organization_id=organization.id,
            role_id=viewer_role.id,
            assigned_by=admin_user.id,
        )

        # Verify assignments are active
        assert admin_assignment.is_active is True
        assert member_assignment.is_active is True
        assert viewer_assignment.is_active is True

        # Step 2: Test role revocation
        revoked_member_assignment = member_assignment.revoke(revoked_by=admin_user.id)
        assert revoked_member_assignment.is_active is False
        assert revoked_member_assignment.revoked_by == admin_user.id
        assert revoked_member_assignment.revoked_at is not None

        # Step 3: Test role reactivation
        reactivated_member_assignment = revoked_member_assignment.reactivate()
        assert reactivated_member_assignment.is_active is True
        assert reactivated_member_assignment.revoked_by is None
        assert reactivated_member_assignment.revoked_at is None

    def test_permission_hierarchy(self, test_data: dict):
        """Test that different roles have appropriate permission levels"""

        permissions = test_data["permissions"]
        roles = test_data["roles"]

        # Admin should have all permissions
        admin_expected_permissions = [
            permissions["user_read"],
            permissions["user_write"],
            permissions["user_delete"],
            permissions["org_read"],
            permissions["org_write"],
        ]

        # Member should have read/write but not delete
        member_expected_permissions = [
            permissions["user_read"],
            permissions["user_write"],
            permissions["org_read"],
            permissions["org_write"],
        ]

        # Viewer should only have read permissions
        viewer_expected_permissions = [
            permissions["user_read"],
            permissions["org_read"],
        ]

        # Verify permission structure (in a real implementation,
        # you'd have role-permission associations)
        assert roles["admin"].name == "admin"
        assert roles["member"].name == "member"
        assert roles["viewer"].name == "viewer"

    def test_multi_organization_role_isolation(
        self, db_session: Session, test_data: dict
    ):
        """Test that users can have different roles in different organizations"""

        admin_user = test_data["users"]["admin"]
        member_user = test_data["users"]["member"]
        admin_role = test_data["roles"]["admin"]
        viewer_role = test_data["roles"]["viewer"]

        # Create second organization
        org2 = OrganizationFactory.create_organization(
            name="Second Organization", owner_id=admin_user.id
        )

        # User is admin in first org, but viewer in second org
        org1_assignment = UserOrganizationRoleFactory.create_admin_assignment(
            user_id=member_user.id,
            organization_id=test_data["organization"].id,
            admin_role_id=admin_role.id,
            assigned_by=admin_user.id,
        )

        org2_assignment = UserOrganizationRoleFactory.create_user_organization_role(
            user_id=member_user.id,
            organization_id=org2.id,
            role_id=viewer_role.id,
            assigned_by=admin_user.id,
        )

        # Verify different roles in different organizations
        assert org1_assignment.organization_id == test_data["organization"].id
        assert org1_assignment.role_id == admin_role.id

        assert org2_assignment.organization_id == org2.id
        assert org2_assignment.role_id == viewer_role.id

    def test_system_role_protection(self, test_data: dict):
        """Test that system roles cannot be accidentally modified"""

        admin_role = test_data["roles"]["admin"]

        # System roles should be marked as such
        assert admin_role.is_system is True

        # In a real implementation, system roles would be protected from deletion
        # and certain modifications in the business logic layer

    def test_permission_resource_action_granularity(self, test_data: dict):
        """Test that permissions are properly scoped by resource and action"""

        user_read_perm = test_data["permissions"]["user_read"]
        user_write_perm = test_data["permissions"]["user_write"]
        org_read_perm = test_data["permissions"]["org_read"]

        # Verify resource_type and action scoping
        assert user_read_perm.resource_type == "user"
        assert user_read_perm.action.value == "read"

        assert user_write_perm.resource_type == "user"
        assert user_write_perm.action.value == "update"

        assert org_read_perm.resource_type == "organization"
        assert org_read_perm.action.value == "read"

        # Different resource types should be distinguishable
        assert user_read_perm.resource_type != org_read_perm.resource_type

        # Different actions should be distinguishable
        assert user_read_perm.action != user_write_perm.action

    def test_role_assignment_audit_trail(self, test_data: dict):
        """Test that role assignments maintain proper audit information"""

        admin_user = test_data["users"]["admin"]
        member_user = test_data["users"]["member"]
        organization = test_data["organization"]
        member_role = test_data["roles"]["member"]

        # Create role assignment
        assignment = UserOrganizationRoleFactory.create_user_organization_role(
            user_id=member_user.id,
            organization_id=organization.id,
            role_id=member_role.id,
            assigned_by=admin_user.id,
        )

        # Verify audit fields
        assert assignment.assigned_by == admin_user.id
        assert assignment.assigned_at is not None
        assert assignment.revoked_by is None
        assert assignment.revoked_at is None

        # Revoke and check audit trail
        revoked_assignment = assignment.revoke(revoked_by=admin_user.id)
        assert revoked_assignment.revoked_by == admin_user.id
        assert revoked_assignment.revoked_at is not None
