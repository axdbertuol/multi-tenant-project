import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from datetime import datetime

from src.infrastructure.database.models import (
    UserOrganizationRoleModel,
    UserModel,
    OrganizationModel,
    RoleModel,
)
from src.domain.entities.user_organization_role import UserOrganizationRole
from tests.factories.user_organization_role_factory import UserOrganizationRoleFactory
from tests.factories.user_factory import UserFactory
from tests.factories.organization_factory import OrganizationFactory
from tests.factories.role_factory import RoleFactory


class TestUserOrganizationRoleRepositoryIntegration:
    """Integration tests for user organization role repository operations"""

    @pytest.fixture
    def db_session(self):
        from src.infrastructure.database.dependencies import get_db

        session = next(get_db())
        yield session
        session.rollback()
        session.close()

    @pytest.fixture
    def test_entities(self, db_session: Session):
        """Create test users, organizations, and roles"""
        # Create test user
        user = UserFactory.create_user(email="test@example.com", name="Test User")
        user_model = UserModel(
            id=user.id,
            email=user.email.value,
            name=user.name,
            password=user.password.hashed_password,
            created_at=user.created_at,
            is_active=user.is_active,
        )

        # Create test organization
        organization = OrganizationFactory.create_organization(
            name="Test Org", owner_id=user.id
        )
        org_model = OrganizationModel(
            id=organization.id,
            name=organization.name,
            description=organization.description,
            owner_id=organization.owner_id,
            created_at=organization.created_at,
            is_active=organization.is_active,
        )

        # Create test role
        role = RoleFactory.create_admin_role()
        role_model = RoleModel(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            created_at=role.created_at,
            is_active=role.is_active,
        )

        db_session.add_all([user_model, org_model, role_model])
        db_session.commit()

        return {"user": user, "organization": organization, "role": role}

    def test_create_user_organization_role_in_database(
        self, db_session: Session, test_entities: dict
    ):
        """Test creating a user organization role and persisting to database"""
        user = test_entities["user"]
        organization = test_entities["organization"]
        role = test_entities["role"]

        user_org_role = UserOrganizationRoleFactory.create_user_organization_role(
            user_id=user.id,
            organization_id=organization.id,
            role_id=role.id,
            assigned_by=user.id,
        )

        # Convert to database model
        user_org_role_model = UserOrganizationRoleModel(
            id=user_org_role.id,
            user_id=user_org_role.user_id,
            organization_id=user_org_role.organization_id,
            role_id=user_org_role.role_id,
            assigned_at=user_org_role.assigned_at,
            assigned_by=user_org_role.assigned_by,
            revoked_at=user_org_role.revoked_at,
            revoked_by=user_org_role.revoked_by,
            is_active=user_org_role.is_active,
        )

        # Save to database
        db_session.add(user_org_role_model)
        db_session.commit()

        # Retrieve from database
        retrieved_role = (
            db_session.query(UserOrganizationRoleModel)
            .filter(UserOrganizationRoleModel.id == user_org_role.id)
            .first()
        )

        assert retrieved_role is not None
        assert retrieved_role.user_id == user.id
        assert retrieved_role.organization_id == organization.id
        assert retrieved_role.role_id == role.id
        assert retrieved_role.assigned_by == user.id
        assert retrieved_role.is_active is True
        assert retrieved_role.revoked_at is None
        assert retrieved_role.revoked_by is None

    def test_find_user_roles_in_organization(
        self, db_session: Session, test_entities: dict
    ):
        """Test finding all roles for a user in a specific organization"""
        user = test_entities["user"]
        organization = test_entities["organization"]
        role = test_entities["role"]

        # Create additional role and assignment
        member_role = RoleFactory.create_member_role()
        member_role_model = RoleModel(
            id=member_role.id,
            name=member_role.name,
            description=member_role.description,
            is_system=member_role.is_system,
            created_at=member_role.created_at,
            is_active=member_role.is_active,
        )
        db_session.add(member_role_model)

        # Create role assignments
        admin_assignment = UserOrganizationRoleFactory.create_user_organization_role(
            user_id=user.id,
            organization_id=organization.id,
            role_id=role.id,
            assigned_by=user.id,
        )

        member_assignment = UserOrganizationRoleFactory.create_user_organization_role(
            user_id=user.id,
            organization_id=organization.id,
            role_id=member_role.id,
            assigned_by=user.id,
        )

        admin_model = UserOrganizationRoleModel(
            id=admin_assignment.id,
            user_id=admin_assignment.user_id,
            organization_id=admin_assignment.organization_id,
            role_id=admin_assignment.role_id,
            assigned_at=admin_assignment.assigned_at,
            assigned_by=admin_assignment.assigned_by,
            is_active=admin_assignment.is_active,
        )

        member_model = UserOrganizationRoleModel(
            id=member_assignment.id,
            user_id=member_assignment.user_id,
            organization_id=member_assignment.organization_id,
            role_id=member_assignment.role_id,
            assigned_at=member_assignment.assigned_at,
            assigned_by=member_assignment.assigned_by,
            is_active=member_assignment.is_active,
        )

        db_session.add_all([admin_model, member_model])
        db_session.commit()

        # Find user roles in organization
        user_roles = (
            db_session.query(UserOrganizationRoleModel)
            .filter(
                UserOrganizationRoleModel.user_id == user.id,
                UserOrganizationRoleModel.organization_id == organization.id,
                UserOrganizationRoleModel.is_active == True,
            )
            .all()
        )

        assert len(user_roles) == 2
        role_ids = [ur.role_id for ur in user_roles]
        assert role.id in role_ids
        assert member_role.id in role_ids

    def test_revoke_user_role_in_database(
        self, db_session: Session, test_entities: dict
    ):
        """Test revoking a user role in database"""
        user = test_entities["user"]
        organization = test_entities["organization"]
        role = test_entities["role"]

        user_org_role = UserOrganizationRoleFactory.create_user_organization_role(
            user_id=user.id,
            organization_id=organization.id,
            role_id=role.id,
            assigned_by=user.id,
        )

        user_org_role_model = UserOrganizationRoleModel(
            id=user_org_role.id,
            user_id=user_org_role.user_id,
            organization_id=user_org_role.organization_id,
            role_id=user_org_role.role_id,
            assigned_at=user_org_role.assigned_at,
            assigned_by=user_org_role.assigned_by,
            is_active=user_org_role.is_active,
        )

        db_session.add(user_org_role_model)
        db_session.commit()

        # Revoke role
        revoked_role = user_org_role.revoke(revoked_by=user.id)

        # Update in database
        user_org_role_model.is_active = revoked_role.is_active
        user_org_role_model.revoked_at = revoked_role.revoked_at
        user_org_role_model.revoked_by = revoked_role.revoked_by
        db_session.commit()

        # Verify revocation
        retrieved_role = (
            db_session.query(UserOrganizationRoleModel)
            .filter(UserOrganizationRoleModel.id == user_org_role.id)
            .first()
        )

        assert retrieved_role.is_active is False
        assert retrieved_role.revoked_at is not None
        assert retrieved_role.revoked_by == user.id

    def test_reactivate_user_role_in_database(
        self, db_session: Session, test_entities: dict
    ):
        """Test reactivating a revoked user role in database"""
        user = test_entities["user"]
        organization = test_entities["organization"]
        role = test_entities["role"]

        user_org_role = UserOrganizationRoleFactory.create_user_organization_role(
            user_id=user.id,
            organization_id=organization.id,
            role_id=role.id,
            assigned_by=user.id,
        )

        user_org_role_model = UserOrganizationRoleModel(
            id=user_org_role.id,
            user_id=user_org_role.user_id,
            organization_id=user_org_role.organization_id,
            role_id=user_org_role.role_id,
            assigned_at=user_org_role.assigned_at,
            assigned_by=user_org_role.assigned_by,
            is_active=user_org_role.is_active,
        )

        db_session.add(user_org_role_model)
        db_session.commit()

        # Revoke and then reactivate
        revoked_role = user_org_role.revoke(revoked_by=user.id)
        reactivated_role = revoked_role.reactivate()

        # Update in database
        user_org_role_model.is_active = reactivated_role.is_active
        user_org_role_model.revoked_at = reactivated_role.revoked_at
        user_org_role_model.revoked_by = reactivated_role.revoked_by
        db_session.commit()

        # Verify reactivation
        retrieved_role = (
            db_session.query(UserOrganizationRoleModel)
            .filter(UserOrganizationRoleModel.id == user_org_role.id)
            .first()
        )

        assert retrieved_role.is_active is True
        assert retrieved_role.revoked_at is None
        assert retrieved_role.revoked_by is None

    def test_find_organization_users_with_role(
        self, db_session: Session, test_entities: dict
    ):
        """Test finding all users with a specific role in an organization"""
        user = test_entities["user"]
        organization = test_entities["organization"]
        role = test_entities["role"]

        # Create another user
        user2 = UserFactory.create_user(email="user2@example.com", name="User 2")
        user2_model = UserModel(
            id=user2.id,
            email=user2.email.value,
            name=user2.name,
            password=user2.password.hashed_password,
            created_at=user2.created_at,
            is_active=user2.is_active,
        )
        db_session.add(user2_model)

        # Assign same role to both users
        assignment1 = UserOrganizationRoleFactory.create_user_organization_role(
            user_id=user.id,
            organization_id=organization.id,
            role_id=role.id,
            assigned_by=user.id,
        )

        assignment2 = UserOrganizationRoleFactory.create_user_organization_role(
            user_id=user2.id,
            organization_id=organization.id,
            role_id=role.id,
            assigned_by=user.id,
        )

        model1 = UserOrganizationRoleModel(
            id=assignment1.id,
            user_id=assignment1.user_id,
            organization_id=assignment1.organization_id,
            role_id=assignment1.role_id,
            assigned_at=assignment1.assigned_at,
            assigned_by=assignment1.assigned_by,
            is_active=assignment1.is_active,
        )

        model2 = UserOrganizationRoleModel(
            id=assignment2.id,
            user_id=assignment2.user_id,
            organization_id=assignment2.organization_id,
            role_id=assignment2.role_id,
            assigned_at=assignment2.assigned_at,
            assigned_by=assignment2.assigned_by,
            is_active=assignment2.is_active,
        )

        db_session.add_all([model1, model2])
        db_session.commit()

        # Find users with admin role in organization
        admin_users = (
            db_session.query(UserOrganizationRoleModel)
            .filter(
                UserOrganizationRoleModel.organization_id == organization.id,
                UserOrganizationRoleModel.role_id == role.id,
                UserOrganizationRoleModel.is_active == True,
            )
            .all()
        )

        assert len(admin_users) == 2
        user_ids = [au.user_id for au in admin_users]
        assert user.id in user_ids
        assert user2.id in user_ids

    def test_role_assignment_audit_trail(
        self, db_session: Session, test_entities: dict
    ):
        """Test that role assignments maintain proper audit information"""
        user = test_entities["user"]
        organization = test_entities["organization"]
        role = test_entities["role"]

        user_org_role = UserOrganizationRoleFactory.create_user_organization_role(
            user_id=user.id,
            organization_id=organization.id,
            role_id=role.id,
            assigned_by=user.id,
        )

        user_org_role_model = UserOrganizationRoleModel(
            id=user_org_role.id,
            user_id=user_org_role.user_id,
            organization_id=user_org_role.organization_id,
            role_id=user_org_role.role_id,
            assigned_at=user_org_role.assigned_at,
            assigned_by=user_org_role.assigned_by,
            is_active=user_org_role.is_active,
        )

        db_session.add(user_org_role_model)
        db_session.commit()

        # Verify audit fields
        retrieved_role = (
            db_session.query(UserOrganizationRoleModel)
            .filter(UserOrganizationRoleModel.id == user_org_role.id)
            .first()
        )

        assert retrieved_role.assigned_by == user.id
        assert retrieved_role.assigned_at is not None
        assert isinstance(retrieved_role.assigned_at, datetime)
        assert retrieved_role.revoked_by is None
        assert retrieved_role.revoked_at is None
