"""
Authentication and authorization tests
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthentication:
    """Test authentication endpoints and security"""
    
    def test_user_registration_success(self, test_client):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "strongpassword123"
        }
        
        response = test_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # Password should not be returned
    
    def test_user_registration_duplicate_email(self, test_client, test_user):
        """Test registration with duplicate email fails"""
        user_data = {
            "email": test_user.email,
            "password": "anotherpassword123"
        }
        
        response = test_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_user_registration_invalid_email(self, test_client):
        """Test registration with invalid email fails"""
        user_data = {
            "email": "invalid-email",
            "password": "password123"
        }
        
        response = test_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_user_login_success(self, test_client, test_user):
        """Test successful user login"""
        login_data = {
            "username": test_user.email,  # OAuth2PasswordRequestForm uses 'username'
            "password": "testpassword123"
        }
        
        response = test_client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_user_login_wrong_password(self, test_client, test_user):
        """Test login with wrong password fails"""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = test_client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_user_login_nonexistent_user(self, test_client):
        """Test login with non-existent user fails"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "somepassword"
        }
        
        response = test_client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_get_current_user_success(self, test_client, auth_headers, test_user):
        """Test getting current user info with valid token"""
        response = test_client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
    
    def test_get_current_user_no_token(self, test_client):
        """Test getting current user without token fails"""
        response = test_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_get_current_user_invalid_token(self, test_client):
        """Test getting current user with invalid token fails"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = test_client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_protected_endpoint_requires_auth(self, test_client):
        """Test that protected endpoints require authentication"""
        # Try to access leads without authentication
        response = test_client.get("/api/v1/leads/")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_protected_endpoint_with_auth(self, test_client, auth_headers):
        """Test that protected endpoints work with valid authentication"""
        response = test_client.get("/api/v1/leads/", headers=auth_headers)
        
        # Should not return 401 (might return 200 with empty results)
        assert response.status_code != 401