import pytest
from httpx import AsyncClient
from src.main import app


@pytest.mark.e2e
class TestUserEndpoints:
    """End-to-end tests for user management endpoints."""
    
    async def create_authenticated_user(self, client, email: str = "auth@example.com"):
        """Helper to create user and return auth headers."""
        signup_data = {
            "email": email,
            "name": "Auth User",
            "password": "password123"
        }
        signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
        token = signup_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}, signup_response.json()["user"]
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, async_client):
        """Test successful user creation."""
        # Arrange
        user_data = {
            "email": "create@example.com",
            "name": "Create User",
            "password": "password123"
        }
        
        # Act
        response = await async_client.post("/api/v1/users", json=user_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        
        assert data["email"] == "create@example.com"
        assert data["name"] == "Create User"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, async_client):
        """Test creating user with duplicate email."""
        # Arrange
        user_data = {
            "email": "duplicate@example.com",
            "name": "User 1",
            "password": "password123"
        }
        
        # Create first user
        await async_client.post("/api/v1/users", json=user_data)
        
        # Try to create second user with same email
        user_data["name"] = "User 2"
        
        # Act
        response = await async_client.post("/api/v1/users", json=user_data)
        
        # Assert
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, async_client):
        """Test getting user by ID."""
        # Arrange - Create user first
        user_data = {
            "email": "getbyid@example.com",
            "name": "Get By ID User",
            "password": "password123"
        }
        create_response = await async_client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]
        
        # Act
        response = await async_client.get(f"/api/v1/users/{user_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == user_id
        assert data["email"] == "getbyid@example.com"
        assert data["name"] == "Get By ID User"
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, async_client):
        """Test getting non-existent user by ID."""
        # Arrange
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
        
        # Act
        response = await async_client.get(f"/api/v1/users/{fake_uuid}")
        
        # Assert
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_all_users(self, async_client):
        """Test getting all users."""
        # Arrange - Create multiple users
        users_data = [
            {"email": "user1@example.com", "name": "User 1", "password": "password123"},
            {"email": "user2@example.com", "name": "User 2", "password": "password123"},
            {"email": "user3@example.com", "name": "User 3", "password": "password123"}
        ]
        
        for user_data in users_data:
            await async_client.post("/api/v1/users", json=user_data)
        
        # Act
        response = await async_client.get("/api/v1/users")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 3
        emails = [user["email"] for user in data]
        assert "user1@example.com" in emails
        assert "user2@example.com" in emails
        assert "user3@example.com" in emails
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, async_client):
        """Test successful user update."""
        # Arrange - Create user first
        user_data = {
            "email": "update@example.com",
            "name": "Original Name",
            "password": "password123"
        }
        create_response = await async_client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]
        
        update_data = {"name": "Updated Name"}
        
        # Act
        response = await async_client.put(f"/api/v1/users/{user_id}", json=update_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == user_id
        assert data["name"] == "Updated Name"
        assert data["email"] == "update@example.com"
        assert data["updated_at"] is not None
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, async_client):
        """Test updating non-existent user."""
        # Arrange
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
        update_data = {"name": "Updated Name"}
        
        # Act
        response = await async_client.put(f"/api/v1/users/{fake_uuid}", json=update_data)
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_user_empty_data(self, async_client):
        """Test updating user with empty data."""
        # Arrange - Create user first
        user_data = {
            "email": "emptyupdate@example.com",
            "name": "Original Name",
            "password": "password123"
        }
        create_response = await async_client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]
        
        update_data = {}
        
        # Act
        response = await async_client.put(f"/api/v1/users/{user_id}", json=update_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Name should remain unchanged
        assert data["name"] == "Original Name"
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, async_client):
        """Test successful user deletion."""
        # Arrange - Create user first
        user_data = {
            "email": "delete@example.com",
            "name": "Delete User",
            "password": "password123"
        }
        create_response = await async_client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]
        
        # Act
        response = await async_client.delete(f"/api/v1/users/{user_id}")
        
        # Assert
        assert response.status_code == 204
        
        # Verify user is deleted
        get_response = await async_client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, async_client):
        """Test deleting non-existent user."""
        # Arrange
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
        
        # Act
        response = await async_client.delete(f"/api/v1/users/{fake_uuid}")
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_activate_user_success(self, async_client):
        """Test successful user activation."""
        # Arrange - Create and deactivate user first
        user_data = {
            "email": "activate@example.com",
            "name": "Activate User",
            "password": "password123"
        }
        create_response = await async_client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]
        
        # Deactivate first
        await async_client.patch(f"/api/v1/users/{user_id}/deactivate")
        
        # Act
        response = await async_client.patch(f"/api/v1/users/{user_id}/activate")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_active"] is True
        assert data["updated_at"] is not None
    
    @pytest.mark.asyncio
    async def test_deactivate_user_success(self, async_client):
        """Test successful user deactivation."""
        # Arrange - Create user first
        user_data = {
            "email": "deactivate@example.com",
            "name": "Deactivate User",
            "password": "password123"
        }
        create_response = await async_client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]
        
        # Act
        response = await async_client.patch(f"/api/v1/users/{user_id}/deactivate")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_active"] is False
        assert data["updated_at"] is not None
    
    @pytest.mark.asyncio
    async def test_user_validation_errors(self, async_client):
        """Test user creation with validation errors."""
        # Test invalid email
        invalid_email_data = {
            "email": "invalid-email",
            "name": "Test User",
            "password": "password123"
        }
        response = await async_client.post("/api/v1/users", json=invalid_email_data)
        assert response.status_code == 422
        
        # Test short password
        short_password_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "short"
        }
        response = await async_client.post("/api/v1/users", json=short_password_data)
        assert response.status_code == 422
        
        # Test empty name
        empty_name_data = {
            "email": "test@example.com",
            "name": "",
            "password": "password123"
        }
        response = await async_client.post("/api/v1/users", json=empty_name_data)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_user_crud_flow(self, async_client):
        """Test complete CRUD flow for users."""
        # 1. Create user
        user_data = {
            "email": "crud@example.com",
            "name": "CRUD User",
            "password": "password123"
        }
        create_response = await async_client.post("/api/v1/users", json=user_data)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # 2. Read user
        get_response = await async_client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["email"] == "crud@example.com"
        
        # 3. Update user
        update_data = {"name": "Updated CRUD User"}
        update_response = await async_client.put(f"/api/v1/users/{user_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated CRUD User"
        
        # 4. Deactivate user
        deactivate_response = await async_client.patch(f"/api/v1/users/{user_id}/deactivate")
        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["is_active"] is False
        
        # 5. Activate user
        activate_response = await async_client.patch(f"/api/v1/users/{user_id}/activate")
        assert activate_response.status_code == 200
        assert activate_response.json()["is_active"] is True
        
        # 6. Delete user
        delete_response = await async_client.delete(f"/api/v1/users/{user_id}")
        assert delete_response.status_code == 204
        
        # 7. Verify deletion
        final_get_response = await async_client.get(f"/api/v1/users/{user_id}")
        assert final_get_response.status_code == 404