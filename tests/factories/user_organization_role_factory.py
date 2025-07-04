from uuid import uuid4
from src.iam.domain.entities.user_organization_role import UserOrganizationRole


class UserOrganizationRoleFactory:
    @staticmethod
    def create_user_organization_role(
        user_id=None, organization_id=None, role_id=None, assigned_by=None
    ) -> UserOrganizationRole:
        return UserOrganizationRole.create(
            user_id=user_id or uuid4(),
            organization_id=organization_id or uuid4(),
            role_id=role_id or uuid4(),
            assigned_by=assigned_by or uuid4(),
        )

    @staticmethod
    def create_admin_assignment(
        user_id=None, organization_id=None, admin_role_id=None, assigned_by=None
    ) -> UserOrganizationRole:
        return UserOrganizationRole.create(
            user_id=user_id or uuid4(),
            organization_id=organization_id or uuid4(),
            role_id=admin_role_id or uuid4(),
            assigned_by=assigned_by or uuid4(),
        )

    @staticmethod
    def create_member_assignment(
        user_id=None, organization_id=None, member_role_id=None, assigned_by=None
    ) -> UserOrganizationRole:
        return UserOrganizationRole.create(
            user_id=user_id or uuid4(),
            organization_id=organization_id or uuid4(),
            role_id=member_role_id or uuid4(),
            assigned_by=assigned_by or uuid4(),
        )
