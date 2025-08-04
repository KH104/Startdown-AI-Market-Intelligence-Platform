"""
Export endpoint tests
"""
import pytest
import io
import csv


class TestExportEndpoints:
    """Test export endpoints"""
    
    def test_export_leads_csv_post_success(self, test_client, auth_headers, test_lead):
        """Test CSV export using POST method"""
        export_request = {
            "lead_ids": [test_lead.id],
            "include_enrichment_data": False,
            "max_records": 1000
        }
        
        response = test_client.post(
            "/api/v1/export/leads/csv",
            json=export_request,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "leads_export_" in response.headers["content-disposition"]
        
        # Parse CSV content
        csv_content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Check headers
        assert "Lead ID" in rows[0]
        assert "Company Name" in rows[0]
        assert "Contact Email" in rows[0]
        assert "Lead Score" in rows[0]
        
        # Check data row
        assert len(rows) == 2  # Header + 1 data row
        data_row = rows[1]
        assert str(test_lead.id) in data_row
        assert str(test_lead.score) in data_row
    
    def test_export_leads_csv_with_enrichment(self, test_client, auth_headers, test_lead):
        """Test CSV export with enrichment data"""
        # First enrich the lead
        test_client.post(f"/api/v1/enrichment/lead/{test_lead.id}", headers=auth_headers)
        
        export_request = {
            "lead_ids": [test_lead.id],
            "include_enrichment_data": True
        }
        
        response = test_client.post(
            "/api/v1/export/leads/csv",
            json=export_request,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Parse CSV and check for enrichment columns
        csv_content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        headers = next(csv_reader)
        
        assert "Contact Phone" in headers
        assert "Contact LinkedIn" in headers
        assert "Job Title" in headers
        assert "Company Insights" in headers
    
    def test_export_leads_csv_with_filters(self, test_client, auth_headers, test_lead):
        """Test CSV export with filtering criteria"""
        export_request = {
            "score_min": 70.0,
            "score_max": 90.0,
            "industry": "Technology",
            "max_records": 500
        }
        
        response = test_client.post(
            "/api/v1/export/leads/csv",
            json=export_request,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    def test_export_leads_csv_get_method(self, test_client, auth_headers, test_lead):
        """Test CSV export using GET method with query parameters"""
        response = test_client.get(
            f"/api/v1/export/leads/csv?score_min=70&industry=Technology&max_records=100",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    def test_export_leads_csv_no_results(self, test_client, auth_headers):
        """Test CSV export when no leads match criteria"""
        export_request = {
            "score_min": 99.0,  # Very high score that no leads will match
            "score_max": 100.0
        }
        
        response = test_client.post(
            "/api/v1/export/leads/csv",
            json=export_request,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "No leads found matching the criteria" in response.json()["detail"]
    
    def test_export_preview_success(self, test_client, auth_headers, test_lead):
        """Test export preview functionality"""
        response = test_client.get(
            "/api/v1/export/leads/preview?score_min=70&industry=Technology",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_count" in data
        assert "sample_data" in data
        assert "filters_applied" in data
        assert "export_ready" in data
        
        if data["total_count"] > 0:
            assert data["export_ready"] == True
            assert len(data["sample_data"]) <= 10  # Should limit to 10 samples
            
            # Check sample data structure
            sample = data["sample_data"][0]
            assert "lead_id" in sample
            assert "company_name" in sample
            assert "score" in sample
    
    def test_export_preview_no_results(self, test_client, auth_headers):
        """Test export preview when no results"""
        response = test_client.get(
            "/api/v1/export/leads/preview?score_min=99",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] == 0
        assert data["export_ready"] == False
        assert len(data["sample_data"]) == 0
    
    def test_export_unauthorized(self, test_client):
        """Test export endpoints without authentication"""
        response = test_client.get("/api/v1/export/leads/csv")
        
        assert response.status_code == 401