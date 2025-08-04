"""
Lead scoring service for calculating lead quality scores
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.models.company import Company


class ScoringService:
    """Service class for lead scoring operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_lead_score(
        self,
        lead: Lead,
        company: Company,
        scoring_criteria: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate lead score (0-100) based on company and user criteria.
        
        Default scoring factors:
        - Industry match: 30 points
        - Location match: 20 points  
        - Funding amount: 25 points
        - Company size: 15 points
        - Data completeness: 10 points
        """
        if not scoring_criteria:
            scoring_criteria = self.get_default_scoring_criteria()
        
        total_score = 0.0
        max_score = 100.0
        
        # Industry scoring (30 points max)
        industry_score = self._score_industry(company, scoring_criteria)
        total_score += industry_score
        
        # Location scoring (20 points max)
        location_score = self._score_location(company, scoring_criteria)
        total_score += location_score
        
        # Funding scoring (25 points max)
        funding_score = self._score_funding(company, scoring_criteria)
        total_score += funding_score
        
        # Company size scoring (15 points max) - based on funding as proxy
        size_score = self._score_company_size(company, scoring_criteria)
        total_score += size_score
        
        # Data completeness scoring (10 points max)
        completeness_score = self._score_data_completeness(lead, company)
        total_score += completeness_score
        
        # Ensure score is within 0-100 range
        final_score = min(max(total_score, 0.0), max_score)
        
        return round(final_score, 2)
    
    def _score_industry(self, company: Company, criteria: Dict[str, Any]) -> float:
        """Score based on industry match (0-30 points)"""
        if not company.industry:
            return 5.0  # Small score for missing data
        
        target_industries = criteria.get("target_industries", [])
        if not target_industries:
            return 15.0  # Default score if no preferences
        
        company_industry = company.industry.lower()
        
        # Exact match
        for industry in target_industries:
            if industry.lower() in company_industry:
                return 30.0
        
        # Partial match for related industries
        tech_industries = ["software", "technology", "tech", "saas", "ai", "data", "cloud"]
        finance_industries = ["finance", "banking", "fintech", "investment", "insurance"]
        healthcare_industries = ["healthcare", "medical", "pharma", "biotech", "health"]
        
        industry_groups = {
            "technology": tech_industries,
            "finance": finance_industries,
            "healthcare": healthcare_industries
        }
        
        for target_industry in target_industries:
            target_lower = target_industry.lower()
            for group_name, group_keywords in industry_groups.items():
                if target_lower in group_keywords:
                    for keyword in group_keywords:
                        if keyword in company_industry:
                            return 20.0  # Partial match
        
        return 10.0  # Different industry
    
    def _score_location(self, company: Company, criteria: Dict[str, Any]) -> float:
        """Score based on location match (0-20 points)"""
        if not company.location:
            return 5.0  # Small score for missing data
        
        target_locations = criteria.get("target_locations", [])
        if not target_locations:
            return 10.0  # Default score if no preferences
        
        company_location = company.location.lower()
        
        # Check for exact matches
        for location in target_locations:
            if location.lower() in company_location:
                return 20.0
        
        # Check for country/region matches
        us_keywords = ["usa", "united states", "us", "california", "new york", "texas", "florida"]
        europe_keywords = ["uk", "germany", "france", "netherlands", "sweden", "europe"]
        
        location_groups = {
            "usa": us_keywords,
            "europe": europe_keywords
        }
        
        for target_location in target_locations:
            target_lower = target_location.lower()
            for group_name, group_keywords in location_groups.items():
                if target_lower in group_keywords:
                    for keyword in group_keywords:
                        if keyword in company_location:
                            return 15.0  # Regional match
        
        return 8.0  # Different location
    
    def _score_funding(self, company: Company, criteria: Dict[str, Any]) -> float:
        """Score based on funding amount (0-25 points)"""
        if not company.funding_amount:
            return 10.0  # Default score for missing data
        
        funding = company.funding_amount
        min_funding = criteria.get("min_funding", 0)
        max_funding = criteria.get("max_funding", float('inf'))
        
        # Check if within target range
        if min_funding <= funding <= max_funding:
            # Score based on funding level
            if funding >= 50_000_000:  # $50M+
                return 25.0
            elif funding >= 10_000_000:  # $10M+
                return 22.0
            elif funding >= 5_000_000:   # $5M+
                return 20.0
            elif funding >= 1_000_000:   # $1M+
                return 18.0
            elif funding >= 100_000:     # $100K+
                return 15.0
            else:
                return 12.0
        
        # Penalize if outside target range
        if funding < min_funding:
            return 8.0  # Too small
        else:
            return 8.0  # Too large
    
    def _score_company_size(self, company: Company, criteria: Dict[str, Any]) -> float:
        """Score based on company size indicators (0-15 points)"""
        # Use funding as proxy for company size
        if not company.funding_amount:
            return 8.0  # Default score
        
        funding = company.funding_amount
        
        # Score based on implied company size
        if funding >= 100_000_000:     # Large enterprise
            return 15.0
        elif funding >= 10_000_000:    # Mid-size
            return 13.0
        elif funding >= 1_000_000:     # Small business
            return 11.0
        elif funding >= 100_000:       # Startup
            return 9.0
        else:                          # Very small
            return 7.0
    
    def _score_data_completeness(self, lead: Lead, company: Company) -> float:
        """Score based on data completeness (0-10 points)"""
        total_fields = 6
        completed_fields = 0
        
        # Check lead data completeness
        if lead.main_contact_email:
            completed_fields += 1
        if lead.enrichment_status == "completed":
            completed_fields += 1
        
        # Check company data completeness
        if company.industry:
            completed_fields += 1
        if company.location:
            completed_fields += 1
        if company.funding_amount:
            completed_fields += 1
        if company.name:
            completed_fields += 1
        
        completeness_ratio = completed_fields / total_fields
        return completeness_ratio * 10.0
    
    def get_default_scoring_criteria(self) -> Dict[str, Any]:
        """Get default scoring criteria"""
        return {
            "target_industries": ["technology", "software", "saas", "fintech"],
            "target_locations": ["usa", "california", "new york", "texas"],
            "min_funding": 100_000,
            "max_funding": 100_000_000
        }
    
    def score_lead_by_id(self, lead_id: int, scoring_criteria: Optional[Dict[str, Any]] = None) -> Optional[float]:
        """Score a lead by ID and update the database"""
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return None
        
        company = self.db.query(Company).filter(Company.id == lead.company_id).first()
        if not company:
            return None
        
        # Calculate score
        score = self.calculate_lead_score(lead, company, scoring_criteria)
        
        # Update lead score in database
        lead.score = score
        self.db.commit()
        self.db.refresh(lead)
        
        return score
    
    def score_leads_batch(self, lead_ids: List[int], scoring_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Score multiple leads in batch"""
        results = {
            "scored": 0,
            "failed": 0,
            "errors": [],
            "scores": {}
        }
        
        for lead_id in lead_ids:
            try:
                score = self.score_lead_by_id(lead_id, scoring_criteria)
                if score is not None:
                    results["scored"] += 1
                    results["scores"][lead_id] = score
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Lead {lead_id} not found")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Lead {lead_id}: {str(e)}")
        
        return results
    
    def rescore_all_leads(self, scoring_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Rescore all leads in the database"""
        leads = self.db.query(Lead).all()
        lead_ids = [lead.id for lead in leads]
        
        return self.score_leads_batch(lead_ids, scoring_criteria)