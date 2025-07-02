import pytest


@pytest.fixture
def test_iam_user_data():
    """Test user data for IAM e2e tests."""
    return {
        "email": "iamtest@example.com",
        "name": "IAM Test User",
        "password": "Password123!",
    }


@pytest.fixture
def test_iam_login_data():
    """Login data for IAM e2e tests."""
    return {"email": "iamtest@example.com", "password": "Password123!"}


@pytest.fixture
def admin_user_data():
    """Admin user data for IAM e2e tests."""
    return {
        "email": "admin@example.com",
        "name": "Admin User",
        "password": "AdminPass123!",
    }


@pytest.fixture
def admin_login_data():
    """Admin login data for IAM e2e tests."""
    return {"email": "admin@example.com", "password": "AdminPass123!"}
