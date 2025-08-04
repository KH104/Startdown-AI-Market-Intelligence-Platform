"""
Sample data loader script for populating the database with test data
"""
import json
import csv
import os
import sys
from typing import List, Dict, Any
from datetime import datetime

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, create_tables
from app.models.user import User
from app.models.company import Company
from app.models.lead import Lead
from app.models.lead_enrichment import LeadEnrichment
from app.auth.security import get_password_hash


class SampleDataLoader:
    """Class for loading sample data into the database"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def load_sample_companies(self) -> List[Company]:
        """Load sample companies with diverse industries and funding stages"""
        sample_companies = [
            # Technology Sector
            {
                "name": "CloudTech Solutions",
                "industry": "Technology",
                "location": "San Francisco, CA",
                "funding_amount": 15000000.0
            },
            {
                "name": "DataFlow Analytics",
                "industry": "Technology",
                "location": "Austin, TX",
                "funding_amount": 8500000.0
            },
            {
                "name": "AI Innovations Corp",
                "industry": "Artificial Intelligence",
                "location": "Seattle, WA",
                "funding_amount": 25000000.0
            },
            {
                "name": "CyberSecure Systems",
                "industry": "Cybersecurity",
                "location": "Boston, MA",
                "funding_amount": 12000000.0
            },
            {
                "name": "DevOps Masters",
                "industry": "Technology",
                "location": "Denver, CO",
                "funding_amount": 3500000.0
            },
            
            # Fintech Sector
            {
                "name": "PaymentFlow Inc",
                "industry": "Fintech",
                "location": "New York, NY",
                "funding_amount": 45000000.0
            },
            {
                "name": "CryptoExchange Pro",
                "industry": "Fintech",
                "location": "Miami, FL",
                "funding_amount": 18000000.0
            },
            {
                "name": "LendingTree Solutions",
                "industry": "Fintech",
                "location": "Charlotte, NC",
                "funding_amount": 7200000.0
            },
            {
                "name": "InsureTech Innovations",
                "industry": "Fintech",
                "location": "Chicago, IL",
                "funding_amount": 9800000.0
            },
            
            # Healthcare Sector
            {
                "name": "HealthTech Digital",
                "industry": "Healthcare",
                "location": "Boston, MA",
                "funding_amount": 22000000.0
            },
            {
                "name": "MedDevice Innovations",
                "industry": "Healthcare",
                "location": "San Diego, CA",
                "funding_amount": 35000000.0
            },
            {
                "name": "Telemedicine Solutions",
                "industry": "Healthcare",
                "location": "Nashville, TN",
                "funding_amount": 11500000.0
            },
            {
                "name": "BioTech Research Labs",
                "industry": "Healthcare",
                "location": "Cambridge, MA",
                "funding_amount": 50000000.0
            },
            
            # E-commerce Sector
            {
                "name": "ShopFlow Commerce",
                "industry": "E-commerce",
                "location": "Los Angeles, CA",
                "funding_amount": 16000000.0
            },
            {
                "name": "MarketPlace Pro",
                "industry": "E-commerce",
                "location": "Portland, OR",
                "funding_amount": 6500000.0
            },
            {
                "name": "DropShip Masters",
                "industry": "E-commerce",
                "location": "Phoenix, AZ",
                "funding_amount": 4200000.0
            },
            
            # SaaS Sector
            {
                "name": "CRM Solutions Plus",
                "industry": "SaaS",
                "location": "Atlanta, GA",
                "funding_amount": 13000000.0
            },
            {
                "name": "ProjectManager Pro",
                "industry": "SaaS",
                "location": "Raleigh, NC",
                "funding_amount": 8900000.0
            },
            {
                "name": "Analytics Dashboard",
                "industry": "SaaS",
                "location": "San Jose, CA",
                "funding_amount": 19500000.0
            },
            {
                "name": "HR Management Suite",
                "industry": "SaaS",
                "location": "Minneapolis, MN",
                "funding_amount": 7800000.0
            },
            
            # Manufacturing Sector
            {
                "name": "SmartFactory Systems",
                "industry": "Manufacturing",
                "location": "Detroit, MI",
                "funding_amount": 28000000.0
            },
            {
                "name": "3D Printing Solutions",
                "industry": "Manufacturing",
                "location": "Cincinnati, OH",
                "funding_amount": 14500000.0
            },
            {
                "name": "Robotics Assembly Co",
                "industry": "Manufacturing",
                "location": "Pittsburgh, PA",
                "funding_amount": 32000000.0
            },
            
            # Education Sector
            {
                "name": "EdTech Learning Platform",
                "industry": "Education",
                "location": "Berkeley, CA",
                "funding_amount": 12500000.0
            },
            {
                "name": "Online University Pro",
                "industry": "Education",
                "location": "Tempe, AZ",
                "funding_amount": 24000000.0
            },
            
            # Green Energy Sector
            {
                "name": "Solar Power Innovations",
                "industry": "Green Energy",
                "location": "Phoenix, AZ",
                "funding_amount": 41000000.0
            },
            {
                "name": "Wind Energy Solutions",
                "industry": "Green Energy",
                "location": "Kansas City, MO",
                "funding_amount": 38500000.0
            },
            
            # Smaller Startups (Lower funding)
            {
                "name": "Local Food Delivery",
                "industry": "Food & Beverage",
                "location": "Sacramento, CA",
                "funding_amount": 850000.0
            },
            {
                "name": "Fitness App Startup",
                "industry": "Health & Fitness",
                "location": "Boulder, CO",
                "funding_amount": 1200000.0
            },
            {
                "name": "Pet Care Services",
                "industry": "Consumer Services",
                "location": "Orlando, FL",
                "funding_amount": 650000.0
            },
            {
                "name": "Travel Planning App",
                "industry": "Travel & Tourism",
                "location": "San Antonio, TX",
                "funding_amount": 2100000.0
            },
            {
                "name": "Real Estate Tech",
                "industry": "Real Estate",
                "location": "Las Vegas, NV",
                "funding_amount": 5600000.0
            }
        ]
        
        created_companies = []
        for company_data in sample_companies:
            # Check if company already exists
            existing_company = self.db.query(Company).filter(
                Company.name == company_data["name"]
            ).first()
            
            if not existing_company:
                company = Company(**company_data)
                self.db.add(company)
                created_companies.append(company)
        
        self.db.commit()
        
        # Refresh all created companies to get their IDs
        for company in created_companies:
            self.db.refresh(company)
        
        print(f"✅ Created {len(created_companies)} sample companies")
        return created_companies
    
    def load_sample_leads(self, companies: List[Company]) -> List[Lead]:
        """Load sample leads for the companies"""
        # Email domains for generating contact emails
        email_patterns = [
            "{first}.{last}@{domain}",
            "{first}@{domain}",
            "{role}@{domain}",
            "contact@{domain}",
            "info@{domain}"
        ]
        
        first_names = [
            "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa",
            "James", "Maria", "William", "Jennifer", "Richard", "Patricia", "Charles",
            "Linda", "Joseph", "Elizabeth", "Thomas", "Barbara", "Christopher", "Susan",
            "Daniel", "Jessica", "Matthew", "Karen", "Anthony", "Nancy", "Mark", "Betty"
        ]
        
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
            "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
        ]
        
        roles = ["ceo", "cto", "vp.sales", "marketing", "operations", "contact", "info", "sales"]
        
        created_leads = []
        
        for company in companies:
            # Generate 1-3 leads per company
            num_leads = min(3, max(1, len(companies) // 10 + 1))
            
            # Generate domain from company name
            domain_name = company.name.lower().replace(" ", "").replace("&", "").replace(",", "")
            domain_name = "".join(c for c in domain_name if c.isalnum())[:15]
            domain = f"{domain_name}.com"
            
            for i in range(num_leads):
                # Generate email
                first_name = first_names[hash(f"{company.id}-{i}") % len(first_names)]
                last_name = last_names[hash(f"{company.id}-{i}-last") % len(last_names)]
                role = roles[hash(f"{company.id}-{i}-role") % len(roles)]
                
                if i == 0:  # First lead gets CEO/executive email
                    email = f"ceo@{domain}"
                elif i == 1:  # Second lead gets role-based email
                    email = f"{role}@{domain}"
                else:  # Third lead gets name-based email
                    email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
                
                # Generate enrichment status
                enrichment_statuses = ["pending", "completed", "in_progress"]
                enrichment_status = enrichment_statuses[hash(f"{company.id}-{i}") % len(enrichment_statuses)]
                
                lead = Lead(
                    company_id=company.id,
                    main_contact_email=email,
                    score=0.0,  # Will be calculated by scoring algorithm
                    enrichment_status=enrichment_status
                )
                
                self.db.add(lead)
                created_leads.append(lead)
        
        self.db.commit()
        
        # Refresh all leads to get their IDs
        for lead in created_leads:
            self.db.refresh(lead)
        
        print(f"✅ Created {len(created_leads)} sample leads")
        return created_leads
    
    def create_sample_users(self) -> List[User]:
        """Create sample users for testing"""
        sample_users = [
            {
                "email": "admin@startdown.com",
                "password": "admin123"
            },
            {
                "email": "sales@startdown.com", 
                "password": "sales123"
            },
            {
                "email": "demo@startdown.com",
                "password": "demo123"
            }
        ]
        
        created_users = []
        for user_data in sample_users:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                User.email == user_data["email"]
            ).first()
            
            if not existing_user:
                user = User(
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"])
                )
                self.db.add(user)
                created_users.append(user)
        
        self.db.commit()
        
        for user in created_users:
            self.db.refresh(user)
        
        print(f"✅ Created {len(created_users)} sample users")
        return created_users
    
    def apply_scoring_to_leads(self, leads: List[Lead]):
        """Apply scoring algorithm to sample leads"""
        from app.services.scoring_service import ScoringService
        
        scoring_service = ScoringService(self.db)
        
        scored_count = 0
        for lead in leads:
            try:
                score = scoring_service.score_lead_by_id(lead.id)
                if score is not None:
                    scored_count += 1
            except Exception as e:
                print(f"Warning: Failed to score lead {lead.id}: {e}")
        
        print(f"✅ Applied scoring to {scored_count} leads")
    
    def create_sample_enrichments(self, leads: List[Lead]):
        """Create sample enrichment data for completed leads"""
        from app.services.enrichment_service import EnrichmentService
        
        enrichment_service = EnrichmentService(self.db)
        
        enriched_count = 0
        for lead in leads:
            if lead.enrichment_status == "completed":
                try:
                    enrichment_service.enrich_lead(lead.id)
                    enriched_count += 1
                except Exception as e:
                    print(f"Warning: Failed to enrich lead {lead.id}: {e}")
        
        print(f"✅ Created enrichment data for {enriched_count} leads")
    
    def export_sample_data_to_json(self, filename: str = "sample_data.json"):
        """Export loaded data to JSON file for backup/sharing"""
        companies = self.db.query(Company).all()
        leads = self.db.query(Lead).all()
        
        data = {
            "companies": [
                {
                    "name": c.name,
                    "industry": c.industry,
                    "location": c.location,
                    "funding_amount": c.funding_amount
                } for c in companies
            ],
            "leads": [
                {
                    "company_id": l.company_id,
                    "main_contact_email": l.main_contact_email,
                    "score": l.score,
                    "enrichment_status": l.enrichment_status
                } for l in leads
            ],
            "generated_at": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Exported sample data to {filename}")
    
    def load_all_sample_data(self):
        """Load all sample data in correct order"""
        print("🚀 Starting sample data loading...")
        
        # Create tables if they don't exist
        create_tables()
        
        # Load data in dependency order
        users = self.create_sample_users()
        companies = self.load_sample_companies()
        leads = self.load_sample_leads(companies)
        
        # Apply AI features
        self.apply_scoring_to_leads(leads)
        self.create_sample_enrichments(leads)
        
        # Export for backup
        self.export_sample_data_to_json()
        
        print(f"""
🎉 Sample data loading completed!
   
📊 Summary:
   - Users: {len(users)}
   - Companies: {len(companies)}
   - Leads: {len(leads)}
   
🔑 Test Users:
   - admin@startdown.com / admin123
   - sales@startdown.com / sales123
   - demo@startdown.com / demo123
   
🌐 Access the API at: http://localhost:8000/docs
        """)


def main():
    """Main function to run the sample data loader"""
    db = SessionLocal()
    try:
        loader = SampleDataLoader(db)
        loader.load_all_sample_data()
    finally:
        db.close()


if __name__ == "__main__":
    main()