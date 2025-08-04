"""
Lead management endpoint tests
"""
import pytest


class TestLeadEndpoints:
    """Test lead management endpoints"""
    
    def test_get_leads_success(self, test_client, auth_headers, test_lead):
        """Test getting leads with basic filtering"""
        response = test_client.get("/api/v1/leads/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert "pagination" in data
        assert "filters_applied" in data
        
        # Should have our test lead
        assert len(data["leads"]) >= 1
        
        lead = data["leads"][0]
        assert "id" in lead
        assert "company" in lead
        assert "score" in lead
    
    def test_get_leads_with_score_filter(self, test_client, auth_headers, test_lead):
        """Test filtering leads by score range"""
        response = test_client.get(
            "/api/v1/leads/?score_min=70&score_max=80",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include our test lead (score 75.5)
        assert len(data["leads"]) >= 1
        
        for lead in data["leads"]:
            assert 70 <= lead["score"] <= 80
    
    def test_get_leads_with_industry_filter(self, test_client, auth_headers, test_lead):
        """Test filtering leads by industry"""
        response = test_client.get(
            "/api/v1/leads/?industry=Technology",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include our test lead
        assert len(data["leads"]) >= 1
        
        for lead in data["leads"]:
            if lead["company"]:
                assert "Technology" in lead["company"]["industry"]
    
    def test_get_leads_with_enrichment_filter(self, test_client, auth_headers, test_lead):
        """Test filtering leads by enrichment status"""
        response = test_client.get(
            "/api/v1/leads/?enrichment_status=completed",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for lead in data["leads"]:
            assert lead["enrichment_status"] == "completed"
    
    def test_get_leads_with_email_filter(self, test_client, auth_headers, test_lead):
        """Test filtering leads by email presence"""
        response = test_client.get(
            "/api/v1/leads/?has_email=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for lead in data["leads"]:
            assert lead["main_contact_email"] is not None
    
    def test_get_leads_with_search(self, test_client, auth_headers, test_lead):
        """Test searching leads by text"""
        response = test_client.get(
            "/api/v1/leads/?search=Test",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find our test company
        assert len(data["leads"]) >= 1
    
    def test_get_leads_with_pagination(self, test_client, auth_headers, test_lead):
        """Test lead pagination"""
        response = test_client.get(
            "/api/v1/leads/?skip=0&limit=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["pagination"]["skip"] == 0
        assert data["pagination"]["limit"] == 5
        assert "total" in data["pagination"]
        assert "has_next" in data["pagination"]
        assert "has_prev" in data["pagination"]
    
    def test_get_leads_sorting(self, test_client, auth_headers, test_lead):
        """Test lead sorting"""
        response = test_client.get(
            "/api/v1/leads/?sort_by=score&sort_order=desc",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check if sorting is applied (scores should be in descending order)
        if len(data["leads"]) > 1:
            scores = [lead["score"] for lead in data["leads"]]
            assert scores == sorted(scores, reverse=True)
    
    def test_get_lead_by_id_success(self, test_client, auth_headers, test_lead):
        """Test getting specific lead by ID"""
        response = test_client.get(
            f"/api/v1/leads/{test_lead.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["lead"]["id"] == test_lead.id
        assert data["lead"]["main_contact_email"] == test_lead.main_contact_email
        assert data["lead"]["score"] == test_lead.score
        assert "company" in data
        assert "enrichment_data" in data
    
    def test_get_lead_by_id_not_found(self, test_client, auth_headers):
        """Test getting non-existent lead"""
        response = test_client.get("/api/v1/leads/99999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Lead not found" in response.json()["detail"]
    
    def test_advanced_search_multiple_industries(self, test_client, auth_headers, test_lead):
        """Test advanced search with multiple industries"""
        response = test_client.get(
            "/api/v1/leads/search/advanced?industries=Technology,Fintech",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total" in data
        assert "filters" in data
        assert data["filters"]["industries"] == "Technology,Fintech"
    
    def test_advanced_search_score_range(self, test_client, auth_headers, test_lead):
        """Test advanced search with score range"""
        response = test_client.get(
            "/api/v1/leads/search/advanced?score_range=70,80",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for result in data["results"]:
            assert 70 <= result["score"] <= 80
    
    def test_advanced_search_funding_range(self, test_client, auth_headers, test_lead):
        """Test advanced search with funding range"""
        response = test_client.get(
            "/api/v1/leads/search/advanced?funding_range=1000000,10000000",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for result in data["results"]:
            if result["company"] and result["company"]["funding_amount"]:
                funding = result["company"]["funding_amount"]
                assert 1000000 <= funding <= 10000000
    
    def test_advanced_search_invalid_range_format(self, test_client, auth_headers):
        """Test advanced search with invalid range format"""
        response = test_client.get(
            "/api/v1/leads/search/advanced?score_range=invalid",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Invalid score_range format" in response.json()["detail"]
    
    def test_get_leads_unauthorized(self, test_client):
        """Test getting leads without authentication"""
        response = test_client.get("/api/v1/leads/")
        
        assert response.status_code == 401