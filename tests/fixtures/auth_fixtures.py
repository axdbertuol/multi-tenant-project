import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from src.domain.entities.user import User
from src.domain.entities.user_session import UserSession
from tests.factories.user_factory import UserFactory
from tests.factories.session_factory import UserSessionFactory


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return UserFactory.create_user(
        email="test@example.com",
        name="Test User",
        password="password123"
    )


@pytest.fixture
def sample_inactive_user():
    """Create a sample inactive user for testing."""
    return UserFactory.create_inactive_user(
        email="inactive@example.com",
        name="Inactive User",
        password="password123"
    )


@pytest.fixture
def sample_user_session(sample_user):
    """Create a sample user session for testing."""
    return UserSessionFactory.create_session(
        user_id=sample_user.id,
        session_token="sample_token_123",
        ip_address="192.168.1.1",
        user_agent="Test Agent/1.0"
    )


@pytest.fixture
def sample_expired_session(sample_user):
    """Create a sample expired session for testing."""
    return UserSessionFactory.create_expired_session(
        user_id=sample_user.id,
        session_token="expired_token_123"
    )


@pytest.fixture
def sample_logged_out_session(sample_user):
    """Create a sample logged out session for testing."""
    return UserSessionFactory.create_logged_out_session(
        user_id=sample_user.id,
        session_token="logged_out_token_123"
    )


@pytest.fixture
def multiple_user_sessions(sample_user):
    """Create multiple sessions for the same user."""
    return UserSessionFactory.create_multiple_sessions(
        count=3,
        user_id=sample_user.id
    )


@pytest.fixture
def auth_headers():
    """Create sample authentication headers."""
    return {
        "Authorization": "Bearer sample_jwt_token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def sample_signup_data():
    """Sample data for user signup."""
    return {
        "email": "newuser@example.com",
        "name": "New User",
        "password": "newpassword123"
    }


@pytest.fixture
def sample_login_data():
    """Sample data for user login."""
    return {
        "email": "test@example.com",
        "password": "password123"
    }


@pytest.fixture
def sample_invalid_login_data():
    """Sample invalid data for user login."""
    return {
        "email": "test@example.com",
        "password": "wrongpassword"
    }


@pytest.fixture
def sample_change_password_data():
    """Sample data for changing password."""
    return {
        "old_password": "password123",
        "new_password": "newpassword456"
    }