import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from src.iam.infrastructure.database.models import (
    UserModel,
    UserSessionModel,
    RoleModel,
    PermissionModel,
    user_role_assignment,
    role_permission_association,
)


class TestSessionValidationEndpoints:
    """End-to-end tests for session validation through API endpoints."""

    @pytest.fixture
    def test_user_data(self):
        """Test user data for registration."""
        return {
            "email": "sessiontest@example.com",
            "name": "Session Test User",
            "password": "Password123!",
        }

    @pytest.fixture
    def login_data(self):
        """Login data for authentication."""
        return {"email": "sessiontest@example.com", "password": "Password123!"}

    def test_session_validation_workflow_e2e(
        self, client, db_session, test_user_data, login_data
    ):
        """Test complete workflow of user registration, login, and session validation."""
        # Step 1: Register user
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        assert response.status_code == 201
        user_data = response.json()
        user_id = user_data["id"]

        # Step 2: Login to get session token
        response = client.post("/api/v1/iam/auth/login", json=login_data)
        assert response.status_code == 200
        auth_data = response.json()
        token = auth_data["access_token"]
        assert token is not None

        # Step 3: Validate session through auth endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 200
        validated_user = response.json()["user"]
        assert validated_user["email"] == test_user_data["email"]

        # Step 4: Try to access user data with valid session
        response = client.get(f"/api/v1/iam/users/{user_id}", headers=headers)
        assert response.status_code == 200

        # Step 5: Try to access with invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/iam/auth/validate", headers=invalid_headers)
        assert response.status_code == 401

    def test_session_validation_with_permissions_e2e(
        self, client, db_session, test_user_data, login_data
    ):
        """Test session validation with role-based permissions."""
        # Register and login user
        client.post("/api/v1/iam/users/", json=test_user_data)
        response = client.post("/api/v1/iam/auth/login", json=login_data)
        auth_data = response.json()
        token = auth_data["access_token"]
        user_id = auth_data["user"]["id"]

        # Create admin role and permission in database
        from sqlalchemy import insert

        # Create role
        admin_role_id = uuid4()
        admin_role_model = RoleModel(
            id=admin_role_id,
            name="admin",
            description="Administrator role",
            created_by=user_id,
            is_active=True,
            is_system_role=False,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(admin_role_model)

        # Create permission
        admin_perm_id = uuid4()
        admin_perm_model = PermissionModel(
            id=admin_perm_id,
            name="admin:manage",
            description="Admin management permission",
            action="manage",
            resource_type="admin",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(admin_perm_model)

        # Assign role to user
        stmt = insert(user_role_assignment).values(
            user_id=user_id,
            role_id=admin_role_id,
            assigned_by=user_id,
            assigned_at=datetime.now(timezone.utc),
            is_active=True,
        )
        db_session.execute(stmt)

        # Assign permission to role
        stmt = insert(role_permission_association).values(
            role_id=admin_role_id,
            permission_id=admin_perm_id,
            assigned_at=datetime.now(timezone.utc),
        )
        db_session.execute(stmt)
        db_session.commit()

        # Test access with valid permissions
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 200

        # Access user management endpoints (would require admin:manage permission)
        response = client.get("/api/v1/iam/users/", headers=headers)
        assert response.status_code == 200  # Should work with admin permissions

    def test_session_expiration_e2e(
        self, client, db_session, test_user_data, login_data
    ):
        """Test session expiration handling."""
        # Register and login user
        client.post("/api/v1/iam/users/", json=test_user_data)
        response = client.post("/api/v1/iam/auth/login", json=login_data)
        auth_data = response.json()
        token = auth_data["access_token"]

        # Manually expire the session in database
        session_model = (
            db_session.query(UserSessionModel).filter_by(session_token=token).first()
        )
        if session_model:
            session_model.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            db_session.commit()

        # Try to validate expired session
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 401

    def test_session_logout_invalidation_e2e(
        self, client, db_session, test_user_data, login_data
    ):
        """Test that logged out sessions are properly invalidated."""
        # Register and login user
        client.post("/api/v1/iam/users/", json=test_user_data)
        response = client.post("/api/v1/iam/auth/login", json=login_data)
        auth_data = response.json()
        token = auth_data["access_token"]

        # Validate session is active
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 200

        # Logout
        logout_data = {"all_sessions": False}
        response = client.post(
            "/api/v1/iam/auth/logout", json=logout_data, headers=headers
        )
        assert response.status_code == 200

        # Try to validate logged out session
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 401

    def test_multiple_sessions_validation_e2e(
        self, client, db_session, test_user_data, login_data
    ):
        """Test validation with multiple active sessions."""
        # Register user
        client.post("/api/v1/iam/users/", json=test_user_data)

        # Login multiple times to create multiple sessions
        tokens = []
        for i in range(3):
            response = client.post("/api/v1/iam/auth/login", json=login_data)
            auth_data = response.json()
            tokens.append(auth_data["access_token"])

        # Validate all sessions are active
        for token in tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/iam/auth/validate", headers=headers)
            assert response.status_code == 200

        # Logout from one session
        headers = {"Authorization": f"Bearer {tokens[0]}"}
        logout_data = {"all_sessions": False}
        response = client.post(
            "/api/v1/iam/auth/logout", json=logout_data, headers=headers
        )
        assert response.status_code == 200

        # First session should be invalid
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 401

        # Other sessions should still be valid
        for token in tokens[1:]:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/iam/auth/validate", headers=headers)
            assert response.status_code == 200

    def test_session_validation_with_inactive_user_e2e(
        self, client, db_session, test_user_data, login_data
    ):
        """Test session validation when user becomes inactive."""
        # Register and login user
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        user_data = response.json()
        user_id = user_data["id"]

        response = client.post("/api/v1/iam/auth/login", json=login_data)
        auth_data = response.json()
        token = auth_data["access_token"]

        # Validate session is active
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 200

        # Deactivate user in database
        user_model = db_session.query(UserModel).filter_by(id=user_id).first()
        if user_model:
            user_model.is_active = False
            db_session.commit()

        # Session validation should fail for inactive user
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 401

    def test_session_refresh_validation_e2e(
        self, client, db_session, test_user_data, login_data
    ):
        """Test session refresh and validation workflow."""
        # Register and login user
        client.post("/api/v1/iam/users/", json=test_user_data)
        response = client.post("/api/v1/iam/auth/login", json=login_data)
        auth_data = response.json()
        original_token = auth_data["access_token"]

        # Validate original session
        headers = {"Authorization": f"Bearer {original_token}"}
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 200

        # Refresh session
        response = client.post("/api/v1/iam/auth/refresh", headers=headers)
        assert response.status_code == 200
        refreshed_auth_data = response.json()
        new_token = refreshed_auth_data["access_token"]

        # Validate new session
        new_headers = {"Authorization": f"Bearer {new_token}"}
        response = client.get("/api/v1/iam/auth/validate", headers=new_headers)
        assert response.status_code == 200

        # Original token should still be valid (refresh doesn't invalidate original)
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 200

    def test_session_validation_with_organization_context_e2e(
        self, client, db_session, test_user_data, login_data
    ):
        """Test session validation within organization context."""
        # Register and login user
        client.post("/api/v1/iam/users/", json=test_user_data)
        response = client.post("/api/v1/iam/auth/login", json=login_data)
        auth_data = response.json()
        token = auth_data["access_token"]
        user_id = auth_data["user"]["id"]

        # Create organization-specific role and permission
        org_id = uuid4()

        # Create organization role
        org_role_id = uuid4()
        org_role_model = RoleModel(
            id=org_role_id,
            name="org_member",
            description="Organization member",
            organization_id=org_id,
            created_by=user_id,
            is_active=True,
            is_system_role=False,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(org_role_model)

        # Create organization permission
        org_perm_id = uuid4()
        org_perm_model = PermissionModel(
            id=org_perm_id,
            name="organization:view",
            description="View organization",
            action="view",
            resource_type="organization",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(org_perm_model)

        # Assign role to user with organization scope
        from sqlalchemy import insert

        stmt = insert(user_role_assignment).values(
            user_id=user_id,
            role_id=org_role_id,
            organization_id=org_id,
            assigned_by=user_id,
            assigned_at=datetime.now(timezone.utc),
            is_active=True,
        )
        db_session.execute(stmt)

        # Assign permission to role
        stmt = insert(role_permission_association).values(
            role_id=org_role_id,
            permission_id=org_perm_id,
            assigned_at=datetime.now(timezone.utc),
        )
        db_session.execute(stmt)
        db_session.commit()

        # Validate session with organization context
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 200

        # Test accessing organization-specific endpoints
        # (This would require implementing organization-specific endpoint protection)
        response = client.get("/api/v1/iam/users/", headers=headers)
        assert response.status_code == 200

    def test_concurrent_session_validation_e2e(
        self, client, db_session, test_user_data, login_data
    ):
        """Test concurrent session validation requests."""
        # Register and login user
        client.post("/api/v1/iam/users/", json=test_user_data)
        response = client.post("/api/v1/iam/auth/login", json=login_data)
        auth_data = response.json()
        token = auth_data["access_token"]

        # Simulate concurrent validation requests
        headers = {"Authorization": f"Bearer {token}"}
        responses = []

        # Make multiple concurrent requests (simulated)
        for _ in range(5):
            response = client.get("/api/v1/iam/auth/validate", headers=headers)
            responses.append(response)

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            user_data = response.json()["user"]
            assert user_data["email"] == test_user_data["email"]
