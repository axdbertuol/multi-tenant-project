import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from src.iam.application.use_cases.session_use_cases import SessionUseCase
from src.iam.infrastructure.iam_unit_of_work import IAMUnitOfWork
from src.iam.domain.entities.user import User
from src.iam.domain.entities.user_session import UserSession
from src.iam.domain.entities.role import Role
from src.iam.domain.entities.permission import Permission
from src.iam.domain.entities.policy import Policy
from src.iam.infrastructure.database.models import (
    UserModel, UserSessionModel, RoleModel, PermissionModel, 
    PolicyModel, user_role_assignment, role_permission_association
)
# Note: Using direct entity creation instead of factories to avoid import issues


class TestSessionUseCaseValidateAccessIntegration:
    """Integration tests for SessionUseCase.validate_session_access with real IAM infrastructure."""

    @pytest.fixture
    def iam_uow(self, db_session):
        """Create IAM Unit of Work with database session."""
        return IAMUnitOfWork(
            db_session, 
            ["user", "user_session", "role", "permission", "policy", "resource"]
        )

    @pytest.fixture
    def session_use_case(self, iam_uow):
        """Create SessionUseCase with real dependencies."""
        return SessionUseCase(iam_uow)

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user in the database."""
        user = User.create(
            email="testuser@example.com",
            name="Test User",
            password="Password123!"
        )
        
        user_model = UserModel(
            id=user.id,
            email=user.email.value,
            name=user.name,
            password_hash=user.password.hashed_password,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
        db_session.add(user_model)
        db_session.commit()
        return user

    @pytest.fixture
    def test_session(self, db_session, test_user):
        """Create a test session in the database."""
        session_token = "test-session-token-123"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        session = UserSession.create(
            user_id=test_user.id,
            session_token=session_token,
            expires_at=expires_at,
            ip_address="127.0.0.1",
            user_agent="Test User Agent"
        )
        
        session_model = UserSessionModel(
            id=session.id,
            user_id=session.user_id,
            session_token=session.session_token,
            status=session.status,
            expires_at=session.expires_at,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            created_at=session.created_at
        )
        db_session.add(session_model)
        db_session.commit()
        return session

    @pytest.fixture
    def test_role(self, db_session, test_user):
        """Create a test role in the database."""
        role = Role.create(
            name="test_role",
            description="Test Role",
            created_by=test_user.id
        )
        
        role_model = RoleModel(
            id=role.id,
            name=role.name.value,
            description=role.description,
            created_by=role.created_by,
            is_active=role.is_active,
            is_system_role=role.is_system_role,
            created_at=role.created_at
        )
        db_session.add(role_model)
        db_session.commit()
        return role

    @pytest.fixture
    def test_permission(self, db_session):
        """Create a test permission in the database."""
        permission = Permission.create(
            name="user:read",
            description="Read user data",
            action="read",
            resource_type="user"
        )
        
        permission_model = PermissionModel(
            id=permission.id,
            name=permission.name.value,
            description=permission.description,
            action=permission.action,
            resource_type=permission.resource_type,
            is_active=permission.is_active,
            created_at=permission.created_at
        )
        db_session.add(permission_model)
        db_session.commit()
        return permission

    def test_validate_session_access_with_invalid_token_integration(self, session_use_case):
        """Test validation with non-existent token in database."""
        result = session_use_case.validate_session_access("non-existent-token")
        assert result is False

    def test_validate_session_access_with_valid_token_no_permissions_integration(
        self, session_use_case, test_session
    ):
        """Test validation with valid token and no required permissions."""
        result = session_use_case.validate_session_access(test_session.session_token)
        assert result is True

    def test_validate_session_access_with_expired_session_integration(
        self, db_session, session_use_case, test_user
    ):
        """Test validation with expired session token."""
        # Create expired session
        expired_session = UserSession.create(
            user_id=test_user.id,
            session_token="expired-token-456",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            ip_address="127.0.0.1",
            user_agent="Test User Agent"
        )
        
        session_model = UserSessionModel(
            id=expired_session.id,
            user_id=expired_session.user_id,
            session_token=expired_session.session_token,
            status=expired_session.status,
            expires_at=expired_session.expires_at,
            ip_address=expired_session.ip_address,
            user_agent=expired_session.user_agent,
            created_at=expired_session.created_at
        )
        db_session.add(session_model)
        db_session.commit()
        
        result = session_use_case.validate_session_access(expired_session.session_token)
        assert result is False

    def test_validate_session_access_with_inactive_user_integration(
        self, db_session, session_use_case
    ):
        """Test validation with valid session but inactive user."""
        # Create inactive user
        inactive_user = User.create(
            email="inactive@example.com",
            name="Inactive User",
            password="Password123!"
        ).deactivate()
        
        user_model = UserModel(
            id=inactive_user.id,
            email=inactive_user.email.value,
            name=inactive_user.name,
            password_hash=inactive_user.password.hashed_password,
            is_active=inactive_user.is_active,
            is_verified=inactive_user.is_verified,
            created_at=inactive_user.created_at
        )
        db_session.add(user_model)
        
        # Create session for inactive user
        session = UserSession.create(
            user_id=inactive_user.id,
            session_token="inactive-user-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ip_address="127.0.0.1",
            user_agent="Test User Agent"
        )
        
        session_model = UserSessionModel(
            id=session.id,
            user_id=session.user_id,
            session_token=session.session_token,
            status=session.status,
            expires_at=session.expires_at,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            created_at=session.created_at
        )
        db_session.add(session_model)
        db_session.commit()
        
        result = session_use_case.validate_session_access(session.session_token)
        assert result is False

    def test_validate_session_access_with_role_based_permissions_integration(
        self, db_session, session_use_case, test_session, test_user, test_role, test_permission
    ):
        """Test validation with role-based permissions in database."""
        # Assign role to user
        from sqlalchemy import insert
        stmt = insert(user_role_assignment).values(
            user_id=test_user.id,
            role_id=test_role.id,
            assigned_by=test_user.id,
            assigned_at=datetime.now(timezone.utc),
            is_active=True
        )
        db_session.execute(stmt)
        
        # Assign permission to role
        stmt = insert(role_permission_association).values(
            role_id=test_role.id,
            permission_id=test_permission.id,
            assigned_at=datetime.now(timezone.utc)
        )
        db_session.execute(stmt)
        db_session.commit()
        
        # Test permission validation
        result = session_use_case.validate_session_access(
            token=test_session.session_token,
            required_permissions=["user:read"]
        )
        
        assert result is True

    def test_validate_session_access_without_required_permission_integration(
        self, db_session, session_use_case, test_session, test_user, test_role
    ):
        """Test validation when user doesn't have required permission."""
        # Assign role to user but no permissions to role
        from sqlalchemy import insert
        stmt = insert(user_role_assignment).values(
            user_id=test_user.id,
            role_id=test_role.id,
            assigned_by=test_user.id,
            assigned_at=datetime.now(timezone.utc),
            is_active=True
        )
        db_session.execute(stmt)
        db_session.commit()
        
        # Test permission validation for permission user doesn't have
        result = session_use_case.validate_session_access(
            token=test_session.session_token,
            required_permissions=["admin:delete"]
        )
        
        assert result is False

    def test_validate_session_access_multiple_permissions_integration(
        self, db_session, session_use_case, test_session, test_user, test_role
    ):
        """Test validation with multiple permissions, some allowed and some not."""
        # Create multiple permissions
        read_permission = Permission.create(
            name="user:read",
            description="Read user data",
            action="read",
            resource_type="user"
        )
        
        write_permission = Permission.create(
            name="user:write",
            description="Write user data",
            action="write",
            resource_type="user"
        )
        
        admin_permission = Permission.create(
            name="admin:delete",
            description="Admin delete",
            action="delete",
            resource_type="admin"
        )
        
        # Add permissions to database
        for perm in [read_permission, write_permission, admin_permission]:
            perm_model = PermissionModel(
                id=perm.id,
                name=perm.name.value,
                description=perm.description,
                action=perm.action,
                resource_type=perm.resource_type,
                is_active=perm.is_active,
                created_at=perm.created_at
            )
            db_session.add(perm_model)
        
        # Assign role to user
        from sqlalchemy import insert
        stmt = insert(user_role_assignment).values(
            user_id=test_user.id,
            role_id=test_role.id,
            assigned_by=test_user.id,
            assigned_at=datetime.now(timezone.utc),
            is_active=True
        )
        db_session.execute(stmt)
        
        # Assign only read and write permissions to role (not admin)
        for perm in [read_permission, write_permission]:
            stmt = insert(role_permission_association).values(
                role_id=test_role.id,
                permission_id=perm.id,
                assigned_at=datetime.now(timezone.utc)
            )
            db_session.execute(stmt)
        
        db_session.commit()
        
        # Test with permissions user has
        result = session_use_case.validate_session_access(
            token=test_session.session_token,
            required_permissions=["user:read", "user:write"]
        )
        assert result is True
        
        # Test with permissions user doesn't have
        result = session_use_case.validate_session_access(
            token=test_session.session_token,
            required_permissions=["user:read", "admin:delete"]
        )
        assert result is False

    def test_validate_session_access_simple_integration(
        self, db_session, session_use_case, test_session, test_user, test_role, test_permission
    ):
        """Test the simplified validation method with database integration."""
        # Setup role and permissions
        from sqlalchemy import insert
        stmt = insert(user_role_assignment).values(
            user_id=test_user.id,
            role_id=test_role.id,
            assigned_by=test_user.id,
            assigned_at=datetime.now(timezone.utc),
            is_active=True
        )
        db_session.execute(stmt)
        
        stmt = insert(role_permission_association).values(
            role_id=test_role.id,
            permission_id=test_permission.id,
            assigned_at=datetime.now(timezone.utc)
        )
        db_session.execute(stmt)
        db_session.commit()
        
        # Test simplified method
        result = session_use_case.validate_session_access_simple(
            token=test_session.session_token,
            action="read",
            resource_type="user"
        )
        
        assert result is True

    def test_get_session_user_permissions_integration(
        self, db_session, session_use_case, test_session, test_user, test_role, test_permission
    ):
        """Test getting user permissions with database integration."""
        # Setup role and permissions
        from sqlalchemy import insert
        stmt = insert(user_role_assignment).values(
            user_id=test_user.id,
            role_id=test_role.id,
            assigned_by=test_user.id,
            assigned_at=datetime.now(timezone.utc),
            is_active=True
        )
        db_session.execute(stmt)
        
        stmt = insert(role_permission_association).values(
            role_id=test_role.id,
            permission_id=test_permission.id,
            assigned_at=datetime.now(timezone.utc)
        )
        db_session.execute(stmt)
        db_session.commit()
        
        # Get user permissions
        permissions = session_use_case.get_session_user_permissions(
            token=test_session.session_token
        )
        
        assert "user:read" in permissions

    def test_validate_session_access_with_organization_scope_integration(
        self, db_session, session_use_case, test_session, test_user
    ):
        """Test validation with organization scope using database."""
        org_id = uuid4()
        
        # Create organization-scoped role
        org_role = Role.create(
            name="org_admin",
            description="Organization Admin",
            created_by=test_user.id,
            organization_id=org_id
        )
        
        org_role_model = RoleModel(
            id=org_role.id,
            name=org_role.name.value,
            description=org_role.description,
            organization_id=org_role.organization_id,
            created_by=org_role.created_by,
            is_active=org_role.is_active,
            is_system_role=org_role.is_system_role,
            created_at=org_role.created_at
        )
        db_session.add(org_role_model)
        
        # Create organization permission
        org_permission = Permission.create(
            name="organization:manage",
            description="Manage organization",
            action="manage",
            resource_type="organization"
        )
        
        org_perm_model = PermissionModel(
            id=org_permission.id,
            name=org_permission.name.value,
            description=org_permission.description,
            action=org_permission.action,
            resource_type=org_permission.resource_type,
            is_active=org_permission.is_active,
            created_at=org_permission.created_at
        )
        db_session.add(org_perm_model)
        
        # Assign role to user with organization scope
        from sqlalchemy import insert
        stmt = insert(user_role_assignment).values(
            user_id=test_user.id,
            role_id=org_role.id,
            organization_id=org_id,
            assigned_by=test_user.id,
            assigned_at=datetime.now(timezone.utc),
            is_active=True
        )
        db_session.execute(stmt)
        
        # Assign permission to role
        stmt = insert(role_permission_association).values(
            role_id=org_role.id,
            permission_id=org_permission.id,
            assigned_at=datetime.now(timezone.utc)
        )
        db_session.execute(stmt)
        db_session.commit()
        
        # Test with correct organization scope
        result = session_use_case.validate_session_access(
            token=test_session.session_token,
            required_permissions=["organization:manage"],
            organization_id=str(org_id)
        )
        
        assert result is True
        
        # Test with different organization scope (should fail)
        different_org_id = uuid4()
        result = session_use_case.validate_session_access(
            token=test_session.session_token,
            required_permissions=["organization:manage"],
            organization_id=str(different_org_id)
        )
        
        assert result is False

    def test_session_token_cleanup_after_validation_integration(
        self, db_session, session_use_case, test_user
    ):
        """Test that session validation works correctly with session cleanup."""
        # Create multiple sessions
        tokens = []
        for i in range(3):
            session = UserSession.create(
                user_id=test_user.id,
                session_token=f"token-{i}",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                ip_address="127.0.0.1",
                user_agent="Test User Agent"
            )
            
            session_model = UserSessionModel(
                id=session.id,
                user_id=session.user_id,
                session_token=session.session_token,
                status=session.status,
                expires_at=session.expires_at,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                created_at=session.created_at
            )
            db_session.add(session_model)
            tokens.append(session.session_token)
        
        db_session.commit()
        
        # Validate all sessions
        for token in tokens:
            result = session_use_case.validate_session_access(token)
            assert result is True
        
        # Clean up expired sessions
        expired_count = session_use_case.cleanup_expired_sessions()
        assert expired_count == 0  # No expired sessions yet
        
        # Sessions should still be valid
        for token in tokens:
            result = session_use_case.validate_session_access(token)
            assert result is True