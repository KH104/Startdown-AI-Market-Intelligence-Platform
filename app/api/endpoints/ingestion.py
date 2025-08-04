"""
Data ingestion endpoints for batch JSON data import
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.company import CompanyBatch, CompanyCreate, CompanyResponse
from app.schemas.lead import LeadBatch, LeadCreate, LeadResponse
from app.services.company_service import CompanyService
from app.services.lead_service import LeadService
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.lead import Lead

router = APIRouter()


@router.post("/companies", response_model=List[CompanyResponse], status_code=status.HTTP_201_CREATED)
async def ingest_companies(
    company_batch: CompanyBatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Batch ingest companies from JSON data.
    Validates input, upserts existing records by name, and creates new ones.
    """
    company_service = CompanyService(db)
    created_companies = []
    
    for company_data in company_batch.companies:
        try:
            # Check if company already exists by name
            existing_company = db.query(Company).filter(Company.name == company_data.name).first()
            
            if existing_company:
                # Update existing company
                company = company_service.update_company(
                    existing_company.id,
                    company_data.dict(exclude_unset=True)
                )
            else:
                # Create new company
                company = company_service.create_company(company_data.dict())
            
            created_companies.append(company)
            
        except Exception as e:
            # Log error but continue processing other companies
            print(f"Error processing company {company_data.name}: {str(e)}")
            continue
    
    return created_companies


@router.post("/leads", response_model=List[LeadResponse], status_code=status.HTTP_201_CREATED)
async def ingest_leads(
    lead_batch: LeadBatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Batch ingest leads from JSON data.
    Validates input, creates leads, and marks those with missing data for enrichment.
    """
    lead_service = LeadService(db)
    created_leads = []
    
    for lead_data in lead_batch.leads:
        try:
            # Validate that company exists
            company = db.query(Company).filter(Company.id == lead_data.company_id).first()
            if not company:
                print(f"Company with ID {lead_data.company_id} not found, skipping lead")
                continue
            
            # Check if lead needs enrichment (missing email)
            lead_dict = lead_data.dict()
            if not lead_dict.get("main_contact_email"):
                lead_dict["enrichment_status"] = "pending"
            else:
                lead_dict["enrichment_status"] = "completed"
            
            # Create lead
            lead = lead_service.create_lead(lead_dict)
            created_leads.append(lead)
            
        except Exception as e:
            # Log error but continue processing other leads
            print(f"Error processing lead for company {lead_data.company_id}: {str(e)}")
            continue
    
    return created_leads


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def ingest_batch_data(
    companies: List[CompanyCreate] = [],
    leads: List[LeadCreate] = [],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Batch ingest both companies and leads in a single request.
    Processes companies first, then leads.
    """
    result = {
        "companies_created": 0,
        "leads_created": 0,
        "errors": []
    }
    
    company_service = CompanyService(db)
    lead_service = LeadService(db)
    
    # Process companies first
    for company_data in companies:
        try:
            existing_company = db.query(Company).filter(Company.name == company_data.name).first()
            
            if existing_company:
                company_service.update_company(
                    existing_company.id,
                    company_data.dict(exclude_unset=True)
                )
            else:
                company_service.create_company(company_data.dict())
                result["companies_created"] += 1
                
        except Exception as e:
            result["errors"].append(f"Company {company_data.name}: {str(e)}")
    
    # Process leads
    for lead_data in leads:
        try:
            company = db.query(Company).filter(Company.id == lead_data.company_id).first()
            if not company:
                result["errors"].append(f"Lead for company {lead_data.company_id}: Company not found")
                continue
            
            lead_dict = lead_data.dict()
            if not lead_dict.get("main_contact_email"):
                lead_dict["enrichment_status"] = "pending"
            
            lead_service.create_lead(lead_dict)
            result["leads_created"] += 1
            
        except Exception as e:
            result["errors"].append(f"Lead for company {lead_data.company_id}: {str(e)}")
    
    return result