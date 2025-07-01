import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from src.iam.infrastructure.iam_unit_of_work import IAMUnitOfWork
from src.iam.domain.entities.user import User
from src.iam.domain.entities.user_session import UserSession
from src.iam.domain.entities.role import Role
from src.iam.domain.entities.permission import Permission
from src.iam.infrastructure.database.models import (
    UserModel, UserSessionModel, RoleModel, PermissionModel,
    user_role_assignment, role_permission_association
)


@pytest.fixture
def iam_uow(db_session):
    """Create IAM Unit of Work with database session."""
    return IAMUnitOfWork(
        db_session, 
        ["user", "user_session", "role", "permission", "policy", "resource"]
    )


@pytest.fixture
def test_iam_user(db_session):
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
def test_iam_session(db_session, test_iam_user):
    """Create a test session in the database."""
    session_token = "test-session-token-123"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    session = UserSession.create(
        user_id=test_iam_user.id,
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
def test_iam_role(db_session, test_iam_user):
    """Create a test role in the database."""
    role = Role.create(
        name="test_role",
        description="Test Role",
        created_by=test_iam_user.id
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
def test_iam_permission(db_session):
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