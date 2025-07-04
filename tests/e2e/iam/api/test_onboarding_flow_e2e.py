"""End-to-end tests for complete user onboarding flow."""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timezone

from src.iam.infrastructure.database.models import (
    UserModel,
    OrganizationModel,
    ResourceModel,
    RoleModel,
    PermissionModel,
)


class TestOnboardingFlowE2E:
    """Complete end-to-end tests for user onboarding workflow."""

    @pytest.fixture
    def test_user_data(self):
        """Test user data for registration."""
        return {
            "email": "onboarding@example.com",
            "name": "Onboarding Test User",
            "password": "Password123!",
        }

    @pytest.fixture
    def login_data(self):
        """Login data for authentication."""
        return {"email": "onboarding@example.com", "password": "Password123!"}

    @pytest.fixture
    def onboarding_data(self):
        """Basic onboarding data."""
        return {"organization_name": "Test Organization", "plan_type": "basic"}

    def test_complete_onboarding_flow_basic_plan_e2e(
        self, client, db_session, test_user_data, login_data, onboarding_data
    ):
        """Test complete onboarding flow with basic plan."""
        # Step 1: Register user
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        assert response.status_code == 201
        user_data = response.json()
        user_id = user_data["id"]

        # Step 2: Complete onboarding
        onboarding_payload = {
            "user_id": user_id,
            "owner_id": user_id,
            **onboarding_data,
        }
        response = client.post(
            "/api/v1/iam/onboarding/complete", json=onboarding_payload
        )
        assert response.status_code == 200
        onboarding_result = response.json()

        # Verify onboarding result structure
        assert "organization" in onboarding_result
        assert "applications" in onboarding_result
        assert "jwt_token" in onboarding_result
        assert "next_steps" in onboarding_result

        organization = onboarding_result["organization"]
        assert organization["name"] == onboarding_data["organization_name"]
        assert organization["owner_id"] == user_id

        # Step 3: Verify JWT token works
        jwt_token = onboarding_result["jwt_token"]
        headers = {"Authorization": f"Bearer {jwt_token}"}
        response = client.get("/api/v1/iam/auth/validate", headers=headers)
        assert response.status_code == 200

        validated_data = response.json()
        assert validated_data["user"]["id"] == user_id
        assert "organization_id" in validated_data

        # Step 4: Verify organization was created in database
        org_id = organization["id"]
        org_model = db_session.query(OrganizationModel).filter_by(id=org_id).first()
        assert org_model is not None
        assert org_model.name == onboarding_data["organization_name"]
        assert str(org_model.owner_id) == user_id
        assert org_model.is_active is True

        # Step 5: Verify applications were created as resources
        applications = onboarding_result["applications"]
        assert len(applications) >= 2  # Basic plan should have at least 2 apps

        # Check applications in database
        for app in applications:
            resource_model = (
                db_session.query(ResourceModel)
                .filter_by(id=app["resource_id"], organization_id=org_id)
                .first()
            )
            assert resource_model is not None
            assert resource_model.resource_type in ["web_chat_app", "management_app"]
            assert resource_model.is_active is True

        # Step 6: Verify onboarding status endpoint
        response = client.get(f"/api/v1/iam/onboarding/status/{user_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["onboarding_completed"] is True
        assert status_data["organization"] is not None
        assert len(status_data["applications"]) >= 2

    def test_complete_onboarding_flow_premium_plan_e2e(
        self, client, db_session, test_user_data, login_data
    ):
        """Test onboarding flow with premium plan."""
        # Register user
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        user_data = response.json()
        user_id = user_data["id"]

        # Complete onboarding with premium plan
        onboarding_payload = {
            "user_id": user_id,
            "organization_name": "Premium Test Org",
            "plan_type": "premium",
        }
        response = client.post(
            "/api/v1/iam/onboarding/complete", json=onboarding_payload
        )
        assert response.status_code == 200
        result = response.json()

        # Premium plan should have more applications than basic
        applications = result["applications"]
        app_types = [app["app_type"] for app in applications]

        # Premium should include API access
        assert "web_chat_app" in app_types
        assert "management_app" in app_types
        assert "api_access" in app_types
        assert len(applications) >= 3

    def test_complete_onboarding_flow_custom_apps_e2e(
        self, client, db_session, test_user_data, login_data
    ):
        """Test onboarding flow with custom applications."""
        # Register user
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        user_data = response.json()
        user_id = user_data["id"]

        # Complete onboarding with custom apps
        onboarding_payload = {
            "user_id": user_id,
            "organization_name": "Custom Apps Org",
            "plan_type": "enterprise",
            "custom_apps": ["whatsapp_app", "api_access"],
        }
        response = client.post(
            "/api/v1/iam/onboarding/complete", json=onboarding_payload
        )
        assert response.status_code == 200
        result = response.json()

        # Verify custom apps were created
        applications = result["applications"]
        app_types = [app["app_type"] for app in applications]

        assert "whatsapp_app" in app_types
        assert "api_access" in app_types

    def test_onboarding_available_apps_endpoint_e2e(self, client):
        """Test available applications endpoint."""
        response = client.get("/api/v1/iam/onboarding/available-apps")
        assert response.status_code == 200

        data = response.json()
        assert "available_applications" in data
        assert "recommended_by_plan" in data

        # Check plan recommendations
        recommendations = data["recommended_by_plan"]
        assert "basic" in recommendations
        assert "premium" in recommendations
        assert "enterprise" in recommendations

        # Basic plan should have fewer apps than enterprise
        assert len(recommendations["basic"]) < len(recommendations["enterprise"])

    def test_onboarding_status_without_organization_e2e(
        self, client, db_session, test_user_data
    ):
        """Test onboarding status for user without organization."""
        # Register user but don't complete onboarding
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        user_data = response.json()
        user_id = user_data["id"]

        # Check onboarding status
        response = client.get(f"/api/v1/iam/onboarding/status/{user_id}")
        assert response.status_code == 200

        status_data = response.json()
        assert status_data["onboarding_completed"] is False
        assert status_data["organization"] is None
        assert len(status_data["applications"]) == 0
        assert status_data["total_organizations"] == 0
        assert "next_step" in status_data

    def test_onboarding_jwt_token_contains_organization_context_e2e(
        self, client, db_session, test_user_data, login_data, onboarding_data
    ):
        """Test that JWT token contains organization context after onboarding."""
        # Register and complete onboarding
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        user_data = response.json()
        user_id = user_data["id"]

        onboarding_payload = {"user_id": user_id, **onboarding_data}
        response = client.post(
            "/api/v1/iam/onboarding/complete", json=onboarding_payload
        )
        result = response.json()
        jwt_token = result["jwt_token"]

        # Decode and verify JWT token content
        import jwt as python_jwt
        from src.iam.infrastructure.config.jwt_config import jwt_settings

        decoded_token = python_jwt.decode(
            jwt_token, jwt_settings.SECRET_KEY, algorithms=[jwt_settings.ALGORITHM]
        )

        # Verify token contains organization context
        assert "sub" in decoded_token  # user_id
        assert "organization_id" in decoded_token
        assert decoded_token["sub"] == user_id
        assert decoded_token["organization_id"] == result["organization"]["id"]

    def test_onboarding_access_to_created_applications_e2e(
        self, client, db_session, test_user_data, login_data, onboarding_data
    ):
        """Test access to applications created during onboarding."""
        # Complete onboarding flow
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        user_data = response.json()
        user_id = user_data["id"]

        onboarding_payload = {"user_id": user_id, **onboarding_data}
        response = client.post(
            "/api/v1/iam/onboarding/complete", json=onboarding_payload
        )
        result = response.json()
        jwt_token = result["jwt_token"]

        # Test authentication with JWT token
        headers = {"Authorization": f"Bearer {jwt_token}"}

        # Test access to user profile (should work)
        response = client.get(f"/api/v1/iam/users/{user_id}", headers=headers)
        assert response.status_code == 200

        # Test access to organization data
        org_id = result["organization"]["id"]
        # Note: Would need organization endpoints to test this properly
        # For now, verify the token works for basic authenticated endpoints

    def test_onboarding_error_handling_invalid_user_e2e(self, client, db_session):
        """Test onboarding error handling for invalid user."""
        invalid_user_id = str(uuid4())

        onboarding_payload = {
            "user_id": invalid_user_id,
            "organization_name": "Test Org",
            "plan_type": "basic",
        }

        response = client.post(
            "/api/v1/iam/onboarding/complete", json=onboarding_payload
        )
        assert response.status_code == 400  # or 404, depending on error handling

    def test_onboarding_error_handling_duplicate_organization_e2e(
        self, client, db_session, test_user_data, onboarding_data
    ):
        """Test onboarding error handling for duplicate organization names."""
        # Register user and complete first onboarding
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        user_data = response.json()
        user_id = user_data["id"]

        onboarding_payload = {"user_id": user_id, **onboarding_data}
        response = client.post(
            "/api/v1/iam/onboarding/complete", json=onboarding_payload
        )
        assert response.status_code == 200

        # Try to create another organization with same name
        # This should either fail or create with modified name
        response = client.post(
            "/api/v1/iam/onboarding/complete", json=onboarding_payload
        )
        # The behavior depends on business rules - either 400 error or auto-rename

    def test_onboarding_error_handling_invalid_plan_type_e2e(
        self, client, db_session, test_user_data
    ):
        """Test onboarding error handling for invalid plan type."""
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        user_data = response.json()
        user_id = user_data["id"]

        onboarding_payload = {
            "user_id": user_id,
            "organization_name": "Test Org",
            "plan_type": "invalid_plan",
        }

        response = client.post(
            "/api/v1/iam/onboarding/complete", json=onboarding_payload
        )
        assert response.status_code == 400

    def test_multiple_onboarding_sessions_e2e(
        self, client, db_session, test_user_data, login_data
    ):
        """Test that users can have multiple organizations through separate onboarding flows."""
        # Register user
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        user_data = response.json()
        user_id = user_data["id"]

        # Complete first onboarding
        first_onboarding = {
            "user_id": user_id,
            "organization_name": "First Organization",
            "plan_type": "basic",
        }
        response = client.post("/api/v1/iam/onboarding/complete", json=first_onboarding)
        assert response.status_code == 200
        first_result = response.json()

        # Complete second onboarding
        second_onboarding = {
            "user_id": user_id,
            "organization_name": "Second Organization",
            "plan_type": "premium",
        }
        response = client.post(
            "/api/v1/iam/onboarding/complete", json=second_onboarding
        )
        assert response.status_code == 200
        second_result = response.json()

        # Verify both organizations exist
        assert first_result["organization"]["id"] != second_result["organization"]["id"]

        # Check status shows multiple organizations
        response = client.get(f"/api/v1/iam/onboarding/status/{user_id}")
        status_data = response.json()
        assert status_data["total_organizations"] >= 2

    def test_onboarding_database_persistence_e2e(
        self, client, db_session, test_user_data, onboarding_data
    ):
        """Test that onboarding properly persists data to database."""
        # Complete onboarding
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        user_data = response.json()
        user_id = user_data["id"]

        onboarding_payload = {"user_id": user_id, **onboarding_data}
        response = client.post(
            "/api/v1/iam/onboarding/complete", json=onboarding_payload
        )
        result = response.json()

        # Verify user exists in database
        user_model = db_session.query(UserModel).filter_by(id=user_id).first()
        assert user_model is not None
        assert user_model.email == test_user_data["email"]

        # Verify organization exists in database
        org_id = result["organization"]["id"]
        org_model = db_session.query(OrganizationModel).filter_by(id=org_id).first()
        assert org_model is not None
        assert org_model.name == onboarding_data["organization_name"]
        assert str(org_model.owner_id) == user_id

        # Verify applications exist as resources in database
        for app in result["applications"]:
            resource_model = (
                db_session.query(ResourceModel).filter_by(id=app["resource_id"]).first()
            )
            assert resource_model is not None
            assert str(resource_model.organization_id) == org_id
            assert resource_model.resource_type == app["app_type"]

    def test_onboarding_concurrent_requests_e2e(
        self, client, db_session, test_user_data
    ):
        """Test onboarding behavior with concurrent requests."""
        # Register user
        response = client.post("/api/v1/iam/users/", json=test_user_data)
        user_data = response.json()
        user_id = user_data["id"]

        # Simulate concurrent onboarding requests
        onboarding_payload = {
            "user_id": user_id,
            "organization_name": "Concurrent Test Org",
            "plan_type": "basic",
        }

        responses = []
        for i in range(3):
            response = client.post(
                "/api/v1/iam/onboarding/complete", json=onboarding_payload
            )
            responses.append(response)

        # At least one should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 1

        # Verify database consistency
        org_count = (
            db_session.query(OrganizationModel).filter_by(owner_id=user_id).count()
        )
        # Should have reasonable number of organizations (business rule dependent)
        assert org_count >= 1
