"""Simple end-to-end tests for basic user functionality."""

import pytest


class TestSimpleUserOnboardingE2E:
    """Simple e2e tests focusing on basic user operations."""

    @pytest.fixture
    def test_user_data(self):
        """Test user data for registration."""
        return {
            "email": "simpletest@example.com",
            "name": "Simple Test User",
            "password": "Password123!",
        }

    def test_user_registration_e2e(self, client, db_session, test_user_data):
        """Test basic user registration."""
        # Step 1: Register user
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        assert response.status_code == 201
        user_data = response.json()
        
        # Verify response structure
        assert "id" in user_data
        assert user_data["email"] == test_user_data["email"]
        assert user_data["name"] == test_user_data["name"]
        assert user_data["is_active"] is True
        assert "created_at" in user_data

    def test_user_login_e2e(self, client, db_session, test_user_data):
        """Test basic user login."""
        # Step 1: Register user first
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        assert response.status_code == 201
        
        # Step 2: Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/iam/auth/login", json=login_data)
        assert response.status_code == 200
        
        auth_data = response.json()
        assert "access_token" in auth_data
        assert "user" in auth_data
        assert auth_data["user"]["email"] == test_user_data["email"]

    def test_auth_validation_e2e(self, client, db_session, test_user_data):
        """Test authentication validation."""
        # Step 1: Register and login
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        assert response.status_code == 201
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/iam/auth/login", json=login_data)
        assert response.status_code == 200
        
        auth_data = response.json()
        token = auth_data["access_token"]
        
        # Step 2: Validate token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 200
        
        validated_data = response.json()
        assert "user" in validated_data
        assert validated_data["user"]["email"] == test_user_data["email"]

    def test_complete_user_workflow_e2e(self, client, db_session, test_user_data):
        """Test complete user workflow: register -> login -> access protected endpoint."""
        # Step 1: Register user
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        assert response.status_code == 201
        user_data = response.json()
        user_id = user_data["id"]
        
        # Step 2: Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/iam/auth/login", json=login_data)
        assert response.status_code == 200
        
        auth_data = response.json()
        token = auth_data["access_token"]
        
        # Step 3: Access user profile (protected endpoint)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/v1/iam/users/{user_id}", headers=headers)
        assert response.status_code == 200
        
        profile_data = response.json()
        assert profile_data["id"] == user_id
        assert profile_data["email"] == test_user_data["email"]