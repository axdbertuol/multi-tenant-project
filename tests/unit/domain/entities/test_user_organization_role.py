import pytest
from datetime import datetime
from uuid import uuid4

from src.domain.entities.user_organization_role import UserOrganizationRole


class TestUserOrganizationRole:
    def test_create_user_organization_role(self):
        user_id = uuid4()
        organization_id = uuid4()
        role_id = uuid4()
        assigned_by = uuid4()
        
        user_org_role = UserOrganizationRole.create(
            user_id=user_id,
            organization_id=organization_id,
            role_id=role_id,
            assigned_by=assigned_by
        )
        
        assert user_org_role.user_id == user_id
        assert user_org_role.organization_id == organization_id
        assert user_org_role.role_id == role_id
        assert user_org_role.assigned_by == assigned_by
        assert user_org_role.is_active is True
        assert user_org_role.revoked_at is None
        assert user_org_role.revoked_by is None
        assert isinstance(user_org_role.id, type(uuid4()))
        assert isinstance(user_org_role.assigned_at, datetime)

    def test_revoke_user_organization_role(self):
        user_id = uuid4()
        organization_id = uuid4()
        role_id = uuid4()
        assigned_by = uuid4()
        revoked_by = uuid4()
        
        user_org_role = UserOrganizationRole.create(
            user_id=user_id,
            organization_id=organization_id,
            role_id=role_id,
            assigned_by=assigned_by
        )
        
        revoked_role = user_org_role.revoke(revoked_by=revoked_by)
        
        assert revoked_role.is_active is False
        assert revoked_role.revoked_by == revoked_by
        assert isinstance(revoked_role.revoked_at, datetime)
        assert revoked_role.id == user_org_role.id
        assert revoked_role.user_id == user_id
        assert revoked_role.organization_id == organization_id
        assert revoked_role.role_id == role_id

    def test_reactivate_user_organization_role(self):
        user_id = uuid4()
        organization_id = uuid4()
        role_id = uuid4()
        assigned_by = uuid4()
        revoked_by = uuid4()
        
        user_org_role = UserOrganizationRole.create(
            user_id=user_id,
            organization_id=organization_id,
            role_id=role_id,
            assigned_by=assigned_by
        )
        
        revoked_role = user_org_role.revoke(revoked_by=revoked_by)
        reactivated_role = revoked_role.reactivate()
        
        assert reactivated_role.is_active is True
        assert reactivated_role.revoked_by is None
        assert reactivated_role.revoked_at is None
        assert reactivated_role.id == user_org_role.id
        assert reactivated_role.user_id == user_id
        assert reactivated_role.organization_id == organization_id
        assert reactivated_role.role_id == role_id

    def test_user_organization_role_immutability(self):
        user_id = uuid4()
        organization_id = uuid4()
        role_id = uuid4()
        assigned_by = uuid4()
        
        user_org_role = UserOrganizationRole.create(
            user_id=user_id,
            organization_id=organization_id,
            role_id=role_id,
            assigned_by=assigned_by
        )
        
        with pytest.raises(Exception):
            user_org_role.user_id = uuid4()

    def test_multiple_operations_preserve_data_integrity(self):
        user_id = uuid4()
        organization_id = uuid4()
        role_id = uuid4()
        assigned_by = uuid4()
        revoked_by = uuid4()
        
        original_role = UserOrganizationRole.create(
            user_id=user_id,
            organization_id=organization_id,
            role_id=role_id,
            assigned_by=assigned_by
        )
        
        revoked_role = original_role.revoke(revoked_by=revoked_by)
        reactivated_role = revoked_role.reactivate()
        
        assert reactivated_role.user_id == original_role.user_id
        assert reactivated_role.organization_id == original_role.organization_id
        assert reactivated_role.role_id == original_role.role_id
        assert reactivated_role.assigned_by == original_role.assigned_by
        assert reactivated_role.assigned_at == original_role.assigned_at
        assert reactivated_role.id == original_role.id