"""
Deployment testing script to validate API functionality
"""
import requests
import json
import time
from typing import Dict, Any


class DeploymentTester:
    """Test suite for validating deployed API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.access_token = None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print("🧪 Starting deployment validation tests...")
        
        results = {
            "timestamp": time.time(),
            "base_url": self.base_url,
            "tests": {}
        }
        
        tests = [
            ("Health Check", self.test_health_check),
            ("API Documentation", self.test_api_docs),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Protected Endpoint Access", self.test_protected_access),
            ("Lead Search", self.test_lead_search),
            ("Lead Enrichment", self.test_lead_enrichment),
            ("Lead Scoring", self.test_lead_scoring),
            ("Data Export", self.test_data_export),
            ("Notification Subscription", self.test_notifications)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"   🔍 Running: {test_name}")
            try:
                result = test_func()
                results["tests"][test_name] = {
                    "status": "PASS",
                    "result": result,
                    "error": None
                }
                print(f"   ✅ {test_name}: PASSED")
                passed += 1
            except Exception as e:
                results["tests"][test_name] = {
                    "status": "FAIL",
                    "result": None,
                    "error": str(e)
                }
                print(f"   ❌ {test_name}: FAILED - {str(e)}")
                failed += 1
        
        results["summary"] = {
            "total": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": f"{(passed/len(tests)*100):.1f}%"
        }
        
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {len(tests)}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Success Rate: {results['summary']['success_rate']}")
        
        if failed == 0:
            print("🎉 All tests passed! Deployment is healthy.")
        else:
            print("⚠️  Some tests failed. Please review the deployment.")
        
        return results
    
    def test_health_check(self) -> Dict[str, Any]:
        """Test basic health endpoint"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        
        data = response.json()
        assert data["status"] == "healthy"
        
        return data
    
    def test_api_docs(self) -> Dict[str, Any]:
        """Test API documentation accessibility"""
        response = self.session.get(f"{self.base_url}/docs")
        response.raise_for_status()
        
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
        
        # Also test OpenAPI schema
        schema_response = self.session.get(f"{self.base_url}/openapi.json")
        schema_response.raise_for_status()
        schema = schema_response.json()
        
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        
        return {"docs_accessible": True, "schema_valid": True}
    
    def test_user_registration(self) -> Dict[str, Any]:
        """Test user registration"""
        test_user_data = {
            "email": f"test-{int(time.time())}@startdown.com",
            "password": "testpassword123"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/register",
            json=test_user_data
        )
        response.raise_for_status()
        
        data = response.json()
        assert "id" in data
        assert data["email"] == test_user_data["email"]
        assert "password" not in data
        
        return data
    
    def test_user_login(self) -> Dict[str, Any]:
        """Test user login with demo account"""
        login_data = {
            "username": "demo@startdown.com",
            "password": "demo123"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            data=login_data
        )
        response.raise_for_status()
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Store token for subsequent tests
        self.access_token = data["access_token"]
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}"
        })
        
        return data
    
    def test_protected_access(self) -> Dict[str, Any]:
        """Test access to protected endpoints"""
        if not self.access_token:
            raise Exception("No access token available")
        
        response = self.session.get(f"{self.base_url}/api/v1/auth/me")
        response.raise_for_status()
        
        data = response.json()
        assert "email" in data
        assert "id" in data
        
        return data
    
    def test_lead_search(self) -> Dict[str, Any]:
        """Test lead search functionality"""
        if not self.access_token:
            raise Exception("No access token available")
        
        response = self.session.get(
            f"{self.base_url}/api/v1/leads/?limit=5&score_min=0"
        )
        response.raise_for_status()
        
        data = response.json()
        assert "leads" in data
        assert "pagination" in data
        assert isinstance(data["leads"], list)
        
        return {
            "leads_found": len(data["leads"]),
            "total": data["pagination"].get("total", 0)
        }
    
    def test_lead_enrichment(self) -> Dict[str, Any]:
        """Test lead enrichment functionality"""
        if not self.access_token:
            raise Exception("No access token available")
        
        # Get pending leads
        response = self.session.get(f"{self.base_url}/api/v1/enrichment/pending")
        response.raise_for_status()
        
        data = response.json()
        pending_count = data.get("count", 0)
        
        if pending_count > 0:
            # Try to enrich the first pending lead
            pending_leads = data.get("pending_leads", [])
            if pending_leads:
                lead_id = pending_leads[0]["id"]
                enrich_response = self.session.post(
                    f"{self.base_url}/api/v1/enrichment/lead/{lead_id}"
                )
                enrich_response.raise_for_status()
                enrich_data = enrich_response.json()
                
                return {
                    "pending_leads": pending_count,
                    "enrichment_test": "success",
                    "enriched_lead_id": lead_id
                }
        
        return {"pending_leads": pending_count, "enrichment_test": "skipped"}
    
    def test_lead_scoring(self) -> Dict[str, Any]:
        """Test lead scoring functionality"""
        if not self.access_token:
            raise Exception("No access token available")
        
        # Get scoring criteria
        response = self.session.get(f"{self.base_url}/api/v1/scoring/criteria/default")
        response.raise_for_status()
        
        criteria_data = response.json()
        assert "default_criteria" in criteria_data
        
        # Test top leads endpoint
        top_response = self.session.get(
            f"{self.base_url}/api/v1/scoring/top-leads?limit=5"
        )
        top_response.raise_for_status()
        
        top_data = top_response.json()
        assert "top_leads" in top_data
        
        return {
            "criteria_available": True,
            "top_leads_count": len(top_data["top_leads"])
        }
    
    def test_data_export(self) -> Dict[str, Any]:
        """Test data export functionality"""
        if not self.access_token:
            raise Exception("No access token available")
        
        # Test export preview
        response = self.session.get(
            f"{self.base_url}/api/v1/export/leads/preview?score_min=0&max_records=10"
        )
        response.raise_for_status()
        
        data = response.json()
        assert "total_count" in data
        assert "export_ready" in data
        
        return {
            "preview_working": True,
            "total_exportable": data["total_count"]
        }
    
    def test_notifications(self) -> Dict[str, Any]:
        """Test notification functionality"""
        if not self.access_token:
            raise Exception("No access token available")
        
        # Get subscription types
        response = self.session.get(f"{self.base_url}/api/v1/notifications/types")
        response.raise_for_status()
        
        types_data = response.json()
        assert "subscription_types" in types_data
        
        # Get user subscriptions
        subs_response = self.session.get(f"{self.base_url}/api/v1/notifications/subscriptions")
        subs_response.raise_for_status()
        
        subs_data = subs_response.json()
        assert isinstance(subs_data, list)
        
        return {
            "types_available": len(types_data["subscription_types"]),
            "user_subscriptions": len(subs_data)
        }


def main():
    """Main function to run deployment tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test StartDown API deployment")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="Base URL of the API to test"
    )
    parser.add_argument(
        "--output",
        help="File to save test results (JSON format)"
    )
    
    args = parser.parse_args()
    
    tester = DeploymentTester(args.url)
    results = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Results saved to: {args.output}")
    
    # Exit with error code if tests failed
    if results["summary"]["failed"] > 0:
        exit(1)


if __name__ == "__main__":
    main()