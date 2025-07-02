import pytest
from unittest.mock import Mock
from uuid import uuid4

from src.iam.domain.entities.user import User
from src.iam.domain.entities.user_session import UserSession
from src.iam.domain.entities.role import Role
from src.iam.domain.entities.permission import Permission


@pytest.fixture
def mock_iam_uow():
    """Create a mock IAM Unit of Work."""
    uow = Mock()
    uow.get_repository = Mock()
    return uow


@pytest.fixture
def mock_iam_repositories(mock_iam_uow):
    """Create mock IAM repositories."""
    user_repo = Mock()
    session_repo = Mock()
    role_repo = Mock()
    permission_repo = Mock()
    policy_repo = Mock()
    resource_repo = Mock()

    mock_iam_uow.get_repository.side_effect = lambda name: {
        "user": user_repo,
        "user_session": session_repo,
        "role": role_repo,
        "permission": permission_repo,
        "policy": policy_repo,
        "resource": resource_repo,
        "role_permission": Mock(),
    }[name]

    return {
        "user": user_repo,
        "session": session_repo,
        "role": role_repo,
        "permission": permission_repo,
        "policy": policy_repo,
        "resource": resource_repo,
    }


@pytest.fixture
def sample_iam_user():
    """Create a sample IAM user for testing."""
    return User.create(
        email="test@example.com", name="Test User", password="Password123!"
    )


@pytest.fixture
def sample_iam_session(sample_iam_user):
    """Create a sample IAM session for testing."""
    from datetime import datetime, timezone, timedelta

    return UserSession.create(
        user_id=sample_iam_user.id,
        session_token="test-session-token-123",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ip_address="127.0.0.1",
        user_agent="Test User Agent",
    )


@pytest.fixture
def sample_iam_role(sample_iam_user):
    """Create a sample IAM role for testing."""
    return Role.create(
        name="test_role", description="Test Role", created_by=sample_iam_user.id
    )


@pytest.fixture
def sample_iam_permission():
    """Create a sample IAM permission for testing."""
    return Permission.create(
        name="user:read",
        description="Read user data",
        action="read",
        resource_type="user",
    )


@pytest.fixture
def valid_session_token():
    """Create a valid session token."""
    return "valid-session-token-123"


@pytest.fixture
def invalid_session_token():
    """Create an invalid session token."""
    return "invalid-session-token-456"
