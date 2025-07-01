import pytest
from httpx import Client
from src.main import app
from tests.fixtures.auth_fixtures import *


@pytest.mark.e2e
class TestAuthEndpoints:
    """End-to-end tests for authentication endpoints."""

    @pytest.mark.io
    def test_signup_success(self, _client: Client):
        """Test successful user signup."""
        # Arrange
        print(str(_client))
        signup_data = {
            "email": "newuser@example.com",
            "name": "New User",
            "password": "password123",
        }

        # Act
        response =  _client.post("/api/v1/auth/signup", json=signup_data)

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["name"] == "New User"
        assert data["user"]["is_active"] is True

    @pytest.mark.io
    def test_signup_duplicate_email(self, _client):
        """Test signup with duplicate email."""
        # Arrange
        signup_data = {
            "email": "duplicate@example.com",
            "name": "User 1",
            "password": "password123",
        }
        # Create first user
        _client.post("/api/v1/auth/signup", json=signup_data)

        # Try to create second user with same email
        signup_data["name"] = "User 2"

        # Act
        response =  _client.post("/api/v1/auth/signup", json=signup_data)

        # Assert
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.io
    def test_signup_invalid_email(self, _client):
        """Test signup with invalid email."""
        # Arrange
        signup_data = {
            "email": "invalid-email",
            "name": "Test User",
            "password": "password123",
        }

        # Act
        response =  _client.post("/api/v1/auth/signup", json=signup_data)

        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.io
    def test_signup_short_password(self, _client):
        """Test signup with short password."""
        # Arrange
        signup_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "short",
        }

        # Act
        response =  _client.post("/api/v1/auth/signup", json=signup_data)

        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.io
    def test_login_success(self, _client):
        """Test successful login."""
        # Arrange - Create user first
        signup_data = {
            "email": "login@example.com",
            "name": "Login User",
            "password": "password123",
        }
        _client.post("/api/v1/auth/signup", json=signup_data)

        login_data = {"email": "login@example.com", "password": "password123"}

        # Act
        response =  _client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "login@example.com"

    @pytest.mark.io
    def test_login_wrong_password(self, _client):
        """Test login with wrong password."""
        # Arrange - Create user first
        signup_data = {
            "email": "wrongpass@example.com",
            "name": "Test User",
            "password": "password123",
        }
        _client.post("/api/v1/auth/signup", json=signup_data)

        login_data = {"email": "wrongpass@example.com", "password": "wrongpassword"}

        # Act
        response =  _client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.io
    def test_login_nonexistent_user(self, _client):
        """Test login with non-existent user."""
        # Arrange
        login_data = {"email": "nonexistent@example.com", "password": "password123"}

        # Act
        response =  _client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.io
    def test_get_current_user_success(self, _client):
        """Test getting current user info with valid token."""
        # Arrange - Create user and login
        signup_data = {
            "email": "current@example.com",
            "name": "Current User",
            "password": "password123",
        }
        signup_response =  _client.post(
            "/api/v1/auth/signup", json=signup_data
        )
        token = signup_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response =  _client.get("/api/v1/auth/me", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["email"] == "current@example.com"
        assert data["name"] == "Current User"
        assert data["is_active"] is True

    @pytest.mark.io
    def test_get_current_user_invalid_token(self, _client):
        """Test getting current user with invalid token."""
        # Arrange
        headers = {"Authorization": "Bearer invalid_token"}

        # Act
        response =  _client.get("/api/v1/auth/me", headers=headers)

        # Assert
        assert response.status_code == 401
        assert "Invalid authentication credentials" in response.json()["detail"]

    @pytest.mark.io
    def test_get_current_user_missing_token(self, _client):
        """Test getting current user without token."""
        # Act
        response =  _client.get("/api/v1/auth/me")

        # Assert
        assert response.status_code == 403  # FastAPI security requirement

    @pytest.mark.io
    def test_verify_token_valid(self, _client):
        """Test token verification with valid token."""
        # Arrange - Create user and get token
        signup_data = {
            "email": "verify@example.com",
            "name": "Verify User",
            "password": "password123",
        }
        signup_response =  _client.post(
            "/api/v1/auth/signup", json=signup_data
        )
        token = signup_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response =  _client.post("/api/v1/auth/verify-token", headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["valid"] is True

    @pytest.mark.io
    def test_verify_token_invalid(self, _client):
        """Test token verification with invalid token."""
        # Arrange
        headers = {"Authorization": "Bearer invalid_token"}

        # Act
        response =  _client.post("/api/v1/auth/verify-token", headers=headers)

        # Assert
        assert response.status_code == 401

    @pytest.mark.io
    def test_logout_success(self, _client):
        """Test successful logout."""
        # Arrange - Create user and login
        signup_data = {
            "email": "logout@example.com",
            "name": "Logout User",
            "password": "password123",
        }
        signup_response =  _client.post(
            "/api/v1/auth/signup", json=signup_data
        )
        token = signup_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        logout_data = {"revoke_all_sessions": False}

        # Act
        response =  _client.post(
            "/api/v1/auth/logout", json=logout_data, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "logged out successfully" in data["message"]
        assert data["revoked_sessions_count"] == 1

        # Verify token is no longer valid
        me_response =  _client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 401

    @pytest.mark.io
    def test_logout_all_sessions(self, _client):
        """Test logging out all sessions."""
        # Arrange - Create user and login multiple times
        signup_data = {
            "email": "logoutall@example.com",
            "name": "Logout All User",
            "password": "password123",
        }
        _client.post("/api/v1/auth/signup", json=signup_data)

        # Login multiple times to create multiple sessions
        login_data = {"email": "logoutall@example.com", "password": "password123"}

        login1 =  _client.post("/api/v1/auth/login", json=login_data)
        login2 =  _client.post("/api/v1/auth/login", json=login_data)

        token1 = login1.json()["access_token"]
        token2 = login2.json()["access_token"]

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Act - Logout all sessions from one session
        logout_data = {"revoke_all_sessions": True}
        response =  _client.post(
            "/api/v1/auth/logout", json=logout_data, headers=headers1
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["revoked_sessions_count"] >= 1

        # Verify other session is also invalid
        me_response =  _client.get("/api/v1/auth/me", headers=headers2)
        assert me_response.status_code == 401

    @pytest.mark.io
    def test_get_user_sessions(self, _client):
        """Test getting user sessions."""
        # Arrange - Create user and login multiple times
        signup_data = {
            "email": "sessions@example.com",
            "name": "Sessions User",
            "password": "password123",
        }
        signup_response =  _client.post(
            "/api/v1/auth/signup", json=signup_data
        )
        token = signup_response.json()["access_token"]

        # Create additional session
        login_data = {"email": "sessions@example.com", "password": "password123"}
        _client.post("/api/v1/auth/login", json=login_data)

        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response =  _client.get("/api/v1/auth/sessions", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "sessions" in data
        assert "total_sessions" in data
        assert "active_sessions" in data
        assert data["total_sessions"] >= 2
        assert data["active_sessions"] >= 2

        # Check session details
        sessions = data["sessions"]
        assert len(sessions) >= 2

        for session in sessions:
            assert "id" in session
            assert "status" in session
            assert "login_at" in session
            assert "expires_at" in session

    @pytest.mark.io
    def test_full_auth_flow(self, _client):
        """Test complete authentication flow."""
        # 1. Signup
        signup_data = {
            "email": "fullflow@example.com",
            "name": "Full Flow User",
            "password": "password123",
        }
        signup_response =  _client.post(
            "/api/v1/auth/signup", json=signup_data
        )
        assert signup_response.status_code == 201

        # 2. Login
        login_data = {"email": "fullflow@example.com", "password": "password123"}
        login_response =  _client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # 3. Access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        me_response =  _client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200

        # 4. Verify token
        verify_response =  _client.post(
            "/api/v1/auth/verify-token", headers=headers
        )
        assert verify_response.status_code == 200

        # 5. Get sessions
        sessions_response =  _client.get(
            "/api/v1/auth/sessions", headers=headers
        )
        assert sessions_response.status_code == 200

        # 6. Logout
        logout_data = {"revoke_all_sessions": False}
        logout_response =  _client.post(
            "/api/v1/auth/logout", json=logout_data, headers=headers
        )
        assert logout_response.status_code == 200

        # 7. Verify token is invalid after logout
        final_me_response =  _client.get("/api/v1/auth/me", headers=headers)
        assert final_me_response.status_code == 401
