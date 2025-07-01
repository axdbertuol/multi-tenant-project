import pytest
from unittest.mock import Mock
from uuid import uuid4

from user.domain.entities.user import User
from user.domain.entities.user_session import UserSession, SessionStatus
from user.domain.value_objects.email import Email
from user.domain.value_objects.password import Password


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User.create(
        email="test@example.com",
        name="Test User",
        password="SecurePass123"
    )


@pytest.fixture
def sample_user_with_id():
    """Create a sample user with specific ID for testing."""
    user = User.create(
        email="test@example.com",
        name="Test User",
        password="SecurePass123"
    )
    return user.model_copy(update={"id": uuid4()})


@pytest.fixture
def sample_email():
    """Create a sample email value object for testing."""
    return Email(value="test@example.com")


@pytest.fixture
def sample_password():
    """Create a sample password value object for testing."""
    return Password.create("SecurePass123")


@pytest.fixture
def sample_session():
    """Create a sample user session for testing."""
    from datetime import datetime, timedelta
    
    return UserSession.create(
        user_id=uuid4(),
        session_token="test_session_token",
        expires_at=datetime.utcnow() + timedelta(hours=24),
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0 Test Browser"
    )


@pytest.fixture
def mock_uow():
    """Create a mock unit of work for testing."""
    mock_uow = Mock()
    mock_uow.__enter__ = Mock(return_value=mock_uow)
    mock_uow.__exit__ = Mock(return_value=None)
    return mock_uow


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository for testing."""
    return Mock()


@pytest.fixture
def mock_session_repository():
    """Create a mock session repository for testing."""
    return Mock()


@pytest.fixture
def configured_mock_uow(mock_uow, mock_user_repository, mock_session_repository):
    """Create a configured mock unit of work with repositories."""
    def get_repository(name):
        if name == "user":
            return mock_user_repository
        elif name == "user_session":
            return mock_session_repository
        return None
    
    mock_uow.get_repository.side_effect = get_repository
    return mock_uow


@pytest.fixture
def user_create_dto():
    """Create a sample UserCreateDTO for testing."""
    from user.application.dtos.user_dto import UserCreateDTO
    
    return UserCreateDTO(
        email="test@example.com",
        name="Test User",
        password="SecurePass123"
    )


@pytest.fixture
def login_dto():
    """Create a sample LoginDTO for testing."""
    from user.application.dtos.auth_dto import LoginDTO
    
    return LoginDTO(
        email="test@example.com",
        password="SecurePass123",
        remember_me=False,
        user_agent="Mozilla/5.0",
        ip_address="192.168.1.1"
    )


# Test data constants
TEST_EMAILS = [
    "user@example.com",
    "test.user@domain.co.uk",
    "admin+tag@company.org"
]

VALID_PASSWORDS = [
    "SecurePass123",
    "MyPassword1",
    "StrongPwd2023"
]

INVALID_PASSWORDS = [
    "short",           # Too short
    "nouppercase123",  # No uppercase
    "NOLOWERCASE123",  # No lowercase
    "NoDigitsHere"     # No digits
]

INVALID_EMAILS = [
    "invalid",
    "@example.com",
    "test@",
    "test.example.com",
    ""
]