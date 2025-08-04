"""
Company data management service
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.company import Company


class CompanyService:
    """Service class for company data operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_companies(
        self,
        skip: int = 0,
        limit: int = 100,
        industry: Optional[str] = None,
        location: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Company]:
        """Get companies with optional filtering"""
        query = self.db.query(Company)
        
        if industry:
            query = query.filter(Company.industry.ilike(f"%{industry}%"))
        
        if location:
            query = query.filter(
                Company.city.ilike(f"%{location}%") |
                Company.state.ilike(f"%{location}%") |
                Company.country.ilike(f"%{location}%")
            )
        
        if search:
            query = query.filter(
                Company.name.ilike(f"%{search}%") |
                Company.description.ilike(f"%{search}%")
            )
        
        return query.offset(skip).limit(limit).all()
    
    def get_company_by_id(self, company_id: int) -> Optional[Company]:
        """Get a specific company by ID"""
        return self.db.query(Company).filter(Company.id == company_id).first()
    
    def create_company(self, company_data: dict) -> Company:
        """Create a new company record"""
        company = Company(**company_data)
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company
    
    def update_company(self, company_id: int, company_data: dict) -> Optional[Company]:
        """Update existing company"""
        company = self.get_company_by_id(company_id)
        if company:
            for key, value in company_data.items():
                setattr(company, key, value)
            self.db.commit()
            self.db.refresh(company)
        return company
    
    def enrich_company_data(self, company_id: int) -> Optional[Company]:
        """Enrich company data using AI and external sources"""
        # TODO: Implement AI-powered enrichment logic
        company = self.get_company_by_id(company_id)
        if company:
            # Calculate data completeness
            total_fields = 20  # Adjust based on important fields
            filled_fields = sum(1 for field in [
                company.name, company.website, company.industry, 
                company.city, company.employee_count
            ] if field is not None)
            company.data_completeness = filled_fields / total_fields
            
            self.db.commit()
            self.db.refresh(company)
        return company