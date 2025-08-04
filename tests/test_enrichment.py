"""
Lead enrichment endpoint tests
"""
import pytest


class TestEnrichmentEndpoints:
    """Test lead enrichment endpoints"""
    
    def test_enrich_single_lead_success(self, test_client, auth_headers, test_lead):
        """Test successful single lead enrichment"""
        response = test_client.post(
            f"/api/v1/enrichment/lead/{test_lead.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["lead_id"] == test_lead.id
        assert data["status"] == "completed"
        assert "enriched_data" in data
        assert "lead" in data
        
        # Check enriched data structure
        enriched_data = data["enriched_data"]
        assert "contact_info" in enriched_data
        assert "company_insights" in enriched_data
        assert "market_intelligence" in enriched_data
        
        # Check lead status update
        assert data["lead"]["enrichment_status"] == "completed"
    
    def test_enrich_single_lead_not_found(self, test_client, auth_headers):
        """Test enriching non-existent lead"""
        response = test_client.post(
            "/api/v1/enrichment/lead/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Lead not found" in response.json()["detail"]
    
    def test_enrich_batch_leads_success(self, test_client, auth_headers, test_lead):
        """Test successful batch lead enrichment"""
        request_data = {"lead_ids": [test_lead.id]}
        
        response = test_client.post(
            "/api/v1/enrichment/batch",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 1
        assert data["enriched"] == 1
        assert data["failed"] == 0
        assert data["status"] == "completed"
        assert len(data["errors"]) == 0
    
    def test_enrich_batch_leads_empty_list(self, test_client, auth_headers):
        """Test batch enrichment with empty lead list"""
        request_data = {"lead_ids": []}
        
        response = test_client.post(
            "/api/v1/enrichment/batch",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "No lead IDs provided" in response.json()["detail"]
    
    def test_enrich_batch_leads_nonexistent(self, test_client, auth_headers):
        """Test batch enrichment with non-existent leads"""
        request_data = {"lead_ids": [99999, 99998]}
        
        response = test_client.post(
            "/api/v1/enrichment/batch",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Leads not found" in response.json()["detail"]
    
    def test_get_pending_leads(self, test_client, auth_headers, test_db, test_company):
        """Test getting leads pending enrichment"""
        from app.models.lead import Lead
        
        # Create a lead with pending status
        pending_lead = Lead(
            company_id=test_company.id,
            main_contact_email=None,
            enrichment_status="pending"
        )
        test_db.add(pending_lead)
        test_db.commit()
        
        response = test_client.get(
            "/api/v1/enrichment/pending",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "pending_leads" in data
        assert "count" in data
        assert data["count"] >= 1
        
        # Check that returned leads have pending status
        for lead in data["pending_leads"]:
            assert lead["enrichment_status"] == "pending"
    
    def test_auto_enrich_pending(self, test_client, auth_headers, test_db, test_company):
        """Test auto-enrichment of pending leads"""
        from app.models.lead import Lead
        
        # Create multiple pending leads
        for i in range(3):
            pending_lead = Lead(
                company_id=test_company.id,
                enrichment_status="pending",
                score=0.0
            )
            test_db.add(pending_lead)
        test_db.commit()
        
        response = test_client.post(
            "/api/v1/enrichment/auto-enrich?limit=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "enriched" in data
        assert data["enriched"] >= 3  # Should enrich at least our 3 leads
        assert "total_processed" in data
        assert "failed" in data
        assert "errors" in data
    
    def test_auto_enrich_no_pending(self, test_client, auth_headers):
        """Test auto-enrichment when no leads are pending"""
        response = test_client.post(
            "/api/v1/enrichment/auto-enrich",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "No pending leads found" in data["message"]
        assert data["enriched"] == 0
    
    def test_get_enrichment_data_success(self, test_client, auth_headers, test_lead):
        """Test getting enrichment data for a lead"""
        # First enrich the lead
        test_client.post(
            f"/api/v1/enrichment/lead/{test_lead.id}",
            headers=auth_headers
        )
        
        # Then get the enrichment data
        response = test_client.get(
            f"/api/v1/enrichment/lead/{test_lead.id}/data",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["lead_id"] == test_lead.id
        assert data["enriched"] == True
        assert "data" in data
        
        # Check enrichment data structure
        enrichment_data = data["data"]
        assert "contact_info" in enrichment_data
        assert "company_insights" in enrichment_data
    
    def test_get_enrichment_data_not_enriched(self, test_client, auth_headers, test_db, test_company):
        """Test getting enrichment data for non-enriched lead"""
        from app.models.lead import Lead
        
        # Create lead without enrichment
        plain_lead = Lead(
            company_id=test_company.id,
            enrichment_status="pending"
        )
        test_db.add(plain_lead)
        test_db.commit()
        test_db.refresh(plain_lead)
        
        response = test_client.get(
            f"/api/v1/enrichment/lead/{plain_lead.id}/data",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["lead_id"] == plain_lead.id
        assert data["enriched"] == False
        assert "No enrichment data available" in data["message"]
    
    def test_get_enrichment_data_lead_not_found(self, test_client, auth_headers):
        """Test getting enrichment data for non-existent lead"""
        response = test_client.get(
            "/api/v1/enrichment/lead/99999/data",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Lead not found" in response.json()["detail"]
    
    def test_enrichment_unauthorized(self, test_client, test_lead):
        """Test enrichment endpoints without authentication"""
        response = test_client.post(f"/api/v1/enrichment/lead/{test_lead.id}")
        
        assert response.status_code == 401