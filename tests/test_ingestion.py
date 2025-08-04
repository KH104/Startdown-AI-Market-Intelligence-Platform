"""
Data ingestion endpoint tests
"""
import pytest


class TestDataIngestion:
    """Test data ingestion endpoints"""
    
    def test_ingest_companies_success(self, test_client, auth_headers, sample_companies_data):
        """Test successful company batch ingestion"""
        batch_data = {"companies": sample_companies_data}
        
        response = test_client.post(
            "/api/v1/ingestion/companies",
            json=batch_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data) == len(sample_companies_data)
        
        # Check first company data
        company = data[0]
        assert company["name"] == sample_companies_data[0]["name"]
        assert company["industry"] == sample_companies_data[0]["industry"]
        assert company["funding_amount"] == sample_companies_data[0]["funding_amount"]
    
    def test_ingest_companies_empty_batch(self, test_client, auth_headers):
        """Test ingesting empty company batch"""
        batch_data = {"companies": []}
        
        response = test_client.post(
            "/api/v1/ingestion/companies",
            json=batch_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        assert response.json() == []
    
    def test_ingest_companies_duplicate_names(self, test_client, auth_headers):
        """Test ingesting companies with duplicate names (should update)"""
        company_data = {
            "name": "TechCorp Solutions",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "funding_amount": 1000000.0
        }
        
        batch_data = {"companies": [company_data]}
        
        # First ingestion
        response1 = test_client.post(
            "/api/v1/ingestion/companies",
            json=batch_data,
            headers=auth_headers
        )
        assert response1.status_code == 201
        
        # Second ingestion with updated funding
        company_data["funding_amount"] = 2000000.0
        response2 = test_client.post(
            "/api/v1/ingestion/companies",
            json=batch_data,
            headers=auth_headers
        )
        assert response2.status_code == 201
        
        # Should still return one company with updated funding
        updated_company = response2.json()[0]
        assert updated_company["funding_amount"] == 2000000.0
    
    def test_ingest_leads_success(self, test_client, auth_headers, test_company, sample_leads_data):
        """Test successful lead batch ingestion"""
        batch_data = {"leads": sample_leads_data}
        
        response = test_client.post(
            "/api/v1/ingestion/leads",
            json=batch_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data) == len(sample_leads_data)
        
        # Check lead data
        lead = data[0]
        assert lead["company_id"] == sample_leads_data[0]["company_id"]
        assert lead["main_contact_email"] == sample_leads_data[0]["main_contact_email"]
        assert lead["score"] == sample_leads_data[0]["score"]
    
    def test_ingest_leads_nonexistent_company(self, test_client, auth_headers):
        """Test ingesting leads with non-existent company ID"""
        lead_data = {
            "company_id": 99999,  # Non-existent company
            "main_contact_email": "test@invalid.com",
            "score": 50.0
        }
        
        batch_data = {"leads": [lead_data]}
        
        response = test_client.post(
            "/api/v1/ingestion/leads",
            json=batch_data,
            headers=auth_headers
        )
        
        # Should return 201 but with empty results (skipped invalid lead)
        assert response.status_code == 201
        assert response.json() == []
    
    def test_ingest_leads_missing_email(self, test_client, auth_headers, test_company):
        """Test ingesting leads without email (should mark for enrichment)"""
        lead_data = {
            "company_id": test_company.id,
            "score": 60.0
            # No email provided
        }
        
        batch_data = {"leads": [lead_data]}
        
        response = test_client.post(
            "/api/v1/ingestion/leads",
            json=batch_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 1
        
        lead = data[0]
        assert lead["enrichment_status"] == "pending"  # Should be marked for enrichment
    
    def test_ingest_batch_combined(self, test_client, auth_headers, sample_companies_data):
        """Test combined batch ingestion of companies and leads"""
        # Note: This endpoint expects separate arrays, not the batch wrapper
        companies = sample_companies_data[:2]  # Take first 2 companies
        leads = []  # Empty leads for this test
        
        response = test_client.post(
            "/api/v1/ingestion/batch",
            json={"companies": companies, "leads": leads},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["companies_created"] == 2
        assert data["leads_created"] == 0
        assert "errors" in data
    
    def test_ingest_companies_unauthorized(self, test_client, sample_companies_data):
        """Test company ingestion without authentication"""
        batch_data = {"companies": sample_companies_data}
        
        response = test_client.post("/api/v1/ingestion/companies", json=batch_data)
        
        assert response.status_code == 401
    
    def test_ingest_companies_invalid_data(self, test_client, auth_headers):
        """Test company ingestion with invalid data"""
        # Missing required 'name' field
        invalid_company = {
            "industry": "Technology",
            "location": "San Francisco, CA"
            # Missing 'name' field
        }
        
        batch_data = {"companies": [invalid_company]}
        
        response = test_client.post(
            "/api/v1/ingestion/companies",
            json=batch_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error