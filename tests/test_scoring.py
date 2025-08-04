"""
Lead scoring endpoint tests
"""
import pytest


class TestScoringEndpoints:
    """Test lead scoring endpoints"""
    
    def test_score_single_lead_success(self, test_client, auth_headers, test_lead):
        """Test successful single lead scoring"""
        response = test_client.post(
            f"/api/v1/scoring/lead/{test_lead.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["lead_id"] == test_lead.id
        assert "score" in data
        assert 0 <= data["score"] <= 100
        assert data["status"] == "completed"
        assert "criteria_used" in data
    
    def test_score_single_lead_custom_criteria(self, test_client, auth_headers, test_lead):
        """Test scoring with custom criteria"""
        custom_criteria = {
            "target_industries": ["Technology", "Software"],
            "target_locations": ["California", "San Francisco"],
            "min_funding": 1000000,
            "max_funding": 10000000
        }
        
        response = test_client.post(
            f"/api/v1/scoring/lead/{test_lead.id}",
            json={"scoring_criteria": custom_criteria},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["lead_id"] == test_lead.id
        assert "score" in data
        assert data["criteria_used"]["target_industries"] == custom_criteria["target_industries"]
    
    def test_score_single_lead_not_found(self, test_client, auth_headers):
        """Test scoring non-existent lead"""
        response = test_client.post(
            "/api/v1/scoring/lead/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Lead not found" in response.json()["detail"]
    
    def test_score_batch_leads_success(self, test_client, auth_headers, test_lead):
        """Test successful batch lead scoring"""
        request_data = {"lead_ids": [test_lead.id]}
        
        response = test_client.post(
            "/api/v1/scoring/batch",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 1
        assert data["scored"] == 1
        assert data["failed"] == 0
        assert str(test_lead.id) in data["scores"]
        assert 0 <= data["scores"][str(test_lead.id)] <= 100
    
    def test_score_batch_leads_empty_list(self, test_client, auth_headers):
        """Test batch scoring with empty lead list"""
        request_data = {"lead_ids": []}
        
        response = test_client.post(
            "/api/v1/scoring/batch",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "No lead IDs provided" in response.json()["detail"]
    
    def test_score_batch_leads_nonexistent(self, test_client, auth_headers):
        """Test batch scoring with non-existent leads"""
        request_data = {"lead_ids": [99999, 99998]}
        
        response = test_client.post(
            "/api/v1/scoring/batch",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Leads not found" in response.json()["detail"]
    
    def test_score_batch_leads_with_custom_criteria(self, test_client, auth_headers, test_lead):
        """Test batch scoring with custom criteria"""
        custom_criteria = {
            "target_industries": ["Technology"],
            "min_funding": 100000
        }
        
        request_data = {
            "lead_ids": [test_lead.id],
            "scoring_criteria": custom_criteria
        }
        
        response = test_client.post(
            "/api/v1/scoring/batch",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["scored"] == 1
        assert data["criteria_used"]["target_industries"] == ["Technology"]
    
    def test_rescore_all_leads(self, test_client, auth_headers, test_lead):
        """Test rescoring all leads in database"""
        response = test_client.post(
            "/api/v1/scoring/rescore-all",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Rescored all leads" in data["message"]
        assert "total_leads" in data
        assert "scored" in data
        assert "failed" in data
        assert data["scored"] >= 1  # Should score at least our test lead
    
    def test_rescore_all_leads_with_criteria(self, test_client, auth_headers, test_lead):
        """Test rescoring all leads with custom criteria"""
        custom_criteria = {
            "target_industries": ["Technology", "Fintech"],
            "target_locations": ["California", "New York"]
        }
        
        response = test_client.post(
            "/api/v1/scoring/rescore-all",
            json={"scoring_criteria": custom_criteria},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["criteria_used"]["target_industries"] == custom_criteria["target_industries"]
    
    def test_get_default_criteria(self, test_client, auth_headers):
        """Test getting default scoring criteria"""
        response = test_client.get(
            "/api/v1/scoring/criteria/default",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "default_criteria" in data
        assert "description" in data
        
        criteria = data["default_criteria"]
        assert "target_industries" in criteria
        assert "target_locations" in criteria
        assert "min_funding" in criteria
        assert "max_funding" in criteria
        
        description = data["description"]
        assert "industry_weight" in description
        assert "location_weight" in description
        assert "funding_weight" in description
    
    def test_get_top_scoring_leads(self, test_client, auth_headers, test_lead):
        """Test getting top scoring leads"""
        response = test_client.get(
            "/api/v1/scoring/top-leads?limit=10&min_score=0",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "top_leads" in data
        assert "count" in data
        assert "filters" in data
        
        # Should include our test lead
        assert data["count"] >= 1
        
        # Check sorting (scores should be in descending order)
        if len(data["top_leads"]) > 1:
            scores = [lead["score"] for lead in data["top_leads"]]
            assert scores == sorted(scores, reverse=True)
        
        # Check data structure
        if data["top_leads"]:
            lead = data["top_leads"][0]
            assert "id" in lead
            assert "score" in lead
            assert "company_id" in lead
            assert "enrichment_status" in lead
    
    def test_get_top_scoring_leads_with_min_score(self, test_client, auth_headers, test_lead):
        """Test getting top leads with minimum score filter"""
        response = test_client.get(
            "/api/v1/scoring/top-leads?min_score=70",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned leads should have score >= 70
        for lead in data["top_leads"]:
            assert lead["score"] >= 70
    
    def test_scoring_unauthorized(self, test_client, test_lead):
        """Test scoring endpoints without authentication"""
        response = test_client.post(f"/api/v1/scoring/lead/{test_lead.id}")
        
        assert response.status_code == 401