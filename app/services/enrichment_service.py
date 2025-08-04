"""
Lead enrichment service for filling missing information
"""
import random
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.models.lead_enrichment import LeadEnrichment
from app.models.company import Company


class EnrichmentService:
    """Service class for lead enrichment operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_mock_email(self, company_name: str, company_domain: Optional[str] = None) -> str:
        """Generate mock email for lead contact"""
        # Mock first and last names
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa", "James", "Maria"]
        last_names = ["Smith", "Johnson", "Brown", "Davis", "Wilson", "Miller", "Moore", "Taylor", "Anderson", "Thomas"]
        
        first_name = random.choice(first_names).lower()
        last_name = random.choice(last_names).lower()
        
        # Generate domain from company name if not provided
        if not company_domain:
            # Clean company name and create domain
            domain_name = company_name.lower().replace(" ", "").replace("&", "").replace(",", "")[:10]
            domain = f"{domain_name}.com"
        else:
            domain = company_domain
        
        return f"{first_name}.{last_name}@{domain}"
    
    def generate_enrichment_data(self, lead: Lead, company: Company) -> Dict[str, Any]:
        """Generate mock enrichment data for a lead"""
        enriched_data = {}
        
        # Add contact email if missing
        if not lead.main_contact_email:
            enriched_data["contact_email"] = self.generate_mock_email(company.name)
        
        # Add mock contact information
        enriched_data["contact_info"] = {
            "phone": f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "linkedin": f"https://linkedin.com/in/{random.choice(['john-smith', 'jane-doe', 'michael-brown', 'sarah-wilson'])}",
            "job_title": random.choice([
                "CEO", "CTO", "VP of Sales", "Marketing Director", 
                "Head of Business Development", "Operations Manager", "Product Manager"
            ])
        }
        
        # Add company insights
        enriched_data["company_insights"] = {
            "employee_growth": random.choice(["growing", "stable", "declining"]),
            "funding_stage": random.choice(["seed", "series_a", "series_b", "series_c", "profitable"]),
            "tech_stack": random.sample([
                "React", "Python", "AWS", "Docker", "PostgreSQL", 
                "MongoDB", "Redis", "Kubernetes", "Node.js", "TypeScript"
            ], k=random.randint(2, 5)),
            "pain_points": random.sample([
                "lead generation", "customer retention", "scaling issues", 
                "automation needs", "data analytics", "security concerns"
            ], k=random.randint(1, 3))
        }
        
        # Add market intelligence
        enriched_data["market_intelligence"] = {
            "competitors": random.sample([
                "Salesforce", "HubSpot", "Pipedrive", "Zendesk", 
                "Intercom", "Slack", "Microsoft", "Google"
            ], k=random.randint(2, 4)),
            "market_size": random.choice(["small", "medium", "large", "enterprise"]),
            "buying_signals": random.sample([
                "job postings", "funding announcement", "product launch", 
                "executive hiring", "partnership news", "expansion plans"
            ], k=random.randint(1, 3))
        }
        
        return enriched_data
    
    def enrich_lead(self, lead_id: int) -> Optional[Lead]:
        """Enrich a single lead with mock data"""
        # Get lead and company
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return None
        
        company = self.db.query(Company).filter(Company.id == lead.company_id).first()
        if not company:
            return None
        
        # Generate enrichment data
        enriched_data = self.generate_enrichment_data(lead, company)
        
        # Update lead with enriched email if missing
        if "contact_email" in enriched_data and not lead.main_contact_email:
            lead.main_contact_email = enriched_data["contact_email"]
        
        # Update enrichment status
        lead.enrichment_status = "completed"
        
        # Create or update enrichment record
        existing_enrichment = self.db.query(LeadEnrichment).filter(
            LeadEnrichment.lead_id == lead_id
        ).first()
        
        if existing_enrichment:
            existing_enrichment.enriched_data = enriched_data
        else:
            enrichment = LeadEnrichment(
                lead_id=lead_id,
                enriched_data=enriched_data
            )
            self.db.add(enrichment)
        
        self.db.commit()
        self.db.refresh(lead)
        
        return lead
    
    def enrich_leads_batch(self, lead_ids: list[int]) -> Dict[str, Any]:
        """Enrich multiple leads in batch"""
        results = {
            "enriched": 0,
            "failed": 0,
            "errors": []
        }
        
        for lead_id in lead_ids:
            try:
                enriched_lead = self.enrich_lead(lead_id)
                if enriched_lead:
                    results["enriched"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Lead {lead_id} not found")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Lead {lead_id}: {str(e)}")
        
        return results
    
    def get_enrichment_data(self, lead_id: int) -> Optional[Dict[str, Any]]:
        """Get enrichment data for a lead"""
        enrichment = self.db.query(LeadEnrichment).filter(
            LeadEnrichment.lead_id == lead_id
        ).first()
        
        if enrichment:
            return enrichment.enriched_data
        return None