"""
Notification endpoint tests
"""
import pytest


class TestNotificationEndpoints:
    """Test notification endpoints"""
    
    def test_create_subscription_success(self, test_client, auth_headers):
        """Test successful notification subscription creation"""
        subscription_data = {
            "subscription_type": "lead_updates",
            "email_enabled": True,
            "filter_criteria": {
                "min_score": 75,
                "industries": ["Technology", "Fintech"]
            }
        }
        
        response = test_client.post(
            "/api/v1/notifications/subscribe",
            json=subscription_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["subscription_type"] == "lead_updates"
        assert data["is_active"] == True
        assert data["email_enabled"] == True
        assert data["filter_criteria"]["min_score"] == 75
        assert "id" in data
        assert "created_at" in data
    
    def test_create_subscription_invalid_type(self, test_client, auth_headers):
        """Test creating subscription with invalid type"""
        subscription_data = {
            "subscription_type": "invalid_type",
            "email_enabled": True
        }
        
        response = test_client.post(
            "/api/v1/notifications/subscribe",
            json=subscription_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Invalid subscription type" in response.json()["detail"]
    
    def test_create_duplicate_subscription(self, test_client, auth_headers):
        """Test creating duplicate subscription fails"""
        subscription_data = {
            "subscription_type": "new_leads",
            "email_enabled": True
        }
        
        # Create first subscription
        response1 = test_client.post(
            "/api/v1/notifications/subscribe",
            json=subscription_data,
            headers=auth_headers
        )
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = test_client.post(
            "/api/v1/notifications/subscribe",
            json=subscription_data,
            headers=auth_headers
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]
    
    def test_get_user_subscriptions(self, test_client, auth_headers):
        """Test getting user subscriptions"""
        # Create a subscription first
        subscription_data = {
            "subscription_type": "company_updates",
            "email_enabled": True
        }
        
        test_client.post(
            "/api/v1/notifications/subscribe",
            json=subscription_data,
            headers=auth_headers
        )
        
        # Get subscriptions
        response = test_client.get(
            "/api/v1/notifications/subscriptions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        
        subscription = data[0]
        assert "id" in subscription
        assert "subscription_type" in subscription
        assert "is_active" in subscription
        assert "filter_criteria" in subscription
    
    def test_update_subscription_success(self, test_client, auth_headers):
        """Test updating subscription"""
        # Create subscription
        subscription_data = {
            "subscription_type": "lead_updates",
            "email_enabled": True
        }
        
        create_response = test_client.post(
            "/api/v1/notifications/subscribe",
            json=subscription_data,
            headers=auth_headers
        )
        subscription_id = create_response.json()["id"]
        
        # Update subscription
        update_data = {
            "is_active": False,
            "filter_criteria": {"min_score": 80}
        }
        
        response = test_client.put(
            f"/api/v1/notifications/subscriptions/{subscription_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_active"] == False
        assert data["filter_criteria"]["min_score"] == 80
    
    def test_update_subscription_not_found(self, test_client, auth_headers):
        """Test updating non-existent subscription"""
        update_data = {"is_active": False}
        
        response = test_client.put(
            "/api/v1/notifications/subscriptions/99999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Subscription not found" in response.json()["detail"]
    
    def test_delete_subscription_success(self, test_client, auth_headers):
        """Test deleting subscription"""
        # Create subscription
        subscription_data = {
            "subscription_type": "new_leads",
            "email_enabled": True
        }
        
        create_response = test_client.post(
            "/api/v1/notifications/subscribe",
            json=subscription_data,
            headers=auth_headers
        )
        subscription_id = create_response.json()["id"]
        
        # Delete subscription
        response = test_client.delete(
            f"/api/v1/notifications/subscriptions/{subscription_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify deletion
        get_response = test_client.get(
            "/api/v1/notifications/subscriptions",
            headers=auth_headers
        )
        subscriptions = get_response.json()
        assert not any(sub["id"] == subscription_id for sub in subscriptions)
    
    def test_delete_subscription_not_found(self, test_client, auth_headers):
        """Test deleting non-existent subscription"""
        response = test_client.delete(
            "/api/v1/notifications/subscriptions/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Subscription not found" in response.json()["detail"]
    
    def test_get_notification_logs(self, test_client, auth_headers):
        """Test getting notification logs"""
        response = test_client.get(
            "/api/v1/notifications/logs?limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "count" in data
        assert isinstance(data["logs"], list)
        assert len(data["logs"]) <= 10
    
    def test_test_notification_success(self, test_client, auth_headers):
        """Test sending test notification"""
        # Create subscription
        subscription_data = {
            "subscription_type": "lead_updates",
            "email_enabled": True
        }
        
        create_response = test_client.post(
            "/api/v1/notifications/subscribe",
            json=subscription_data,
            headers=auth_headers
        )
        subscription_id = create_response.json()["id"]
        
        # Send test notification
        response = test_client.post(
            f"/api/v1/notifications/test/{subscription_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Test notification sent" in data["message"]
        assert "log_id" in data
        assert "delivery_status" in data
    
    def test_test_notification_not_found(self, test_client, auth_headers):
        """Test sending test notification for non-existent subscription"""
        response = test_client.post(
            "/api/v1/notifications/test/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Subscription not found" in response.json()["detail"]
    
    def test_get_subscription_types(self, test_client):
        """Test getting available subscription types"""
        response = test_client.get("/api/v1/notifications/types")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "subscription_types" in data
        types = data["subscription_types"]
        
        # Check that all expected types are present
        type_names = [t["type"] for t in types]
        assert "lead_updates" in type_names
        assert "company_updates" in type_names
        assert "new_leads" in type_names
        
        # Check structure of type info
        for type_info in types:
            assert "type" in type_info
            assert "name" in type_info
            assert "description" in type_info
            assert "filter_options" in type_info
    
    def test_notifications_unauthorized(self, test_client):
        """Test notification endpoints without authentication"""
        response = test_client.get("/api/v1/notifications/subscriptions")
        
        assert response.status_code == 401