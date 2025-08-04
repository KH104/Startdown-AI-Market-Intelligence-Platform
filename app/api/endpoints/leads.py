"""
Lead generation and management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from app.database import get_db
from app.models.lead import Lead
from app.models.company import Company
from app.schemas.lead import LeadResponse, LeadWithCompany
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=dict)
async def get_leads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    # Pagination
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    # Lead filters
    score_min: Optional[float] = Query(None, ge=0, le=100, description="Minimum lead score"),
    score_max: Optional[float] = Query(None, ge=0, le=100, description="Maximum lead score"),
    enrichment_status: Optional[str] = Query(None, description="Filter by enrichment status"),
    has_email: Optional[bool] = Query(None, description="Filter leads with/without email"),
    # Company filters
    industry: Optional[str] = Query(None, description="Filter by company industry"),
    location: Optional[str] = Query(None, description="Filter by company location"),
    funding_min: Optional[float] = Query(None, ge=0, description="Minimum company funding"),
    funding_max: Optional[float] = Query(None, ge=0, description="Maximum company funding"),
    # Search
    search: Optional[str] = Query(None, description="Search in company names and contact emails"),
    # Sorting
    sort_by: Optional[str] = Query("score", description="Sort by: score, company_name, funding"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc")
):
    """
    Get list of leads with comprehensive filtering, search, and pagination.
    Returns leads with company information sorted by relevance.
    """
    # Build base query with company join
    query = db.query(Lead).join(Company, Lead.company_id == Company.id)
    
    # Apply lead filters
    if score_min is not None:
        query = query.filter(Lead.score >= score_min)
    
    if score_max is not None:
        query = query.filter(Lead.score <= score_max)
    
    if enrichment_status:
        query = query.filter(Lead.enrichment_status == enrichment_status)
    
    if has_email is not None:
        if has_email:
            query = query.filter(Lead.main_contact_email.isnot(None))
        else:
            query = query.filter(Lead.main_contact_email.is_(None))
    
    # Apply company filters
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))
    
    if location:
        query = query.filter(Company.location.ilike(f"%{location}%"))
    
    if funding_min is not None:
        query = query.filter(Company.funding_amount >= funding_min)
    
    if funding_max is not None:
        query = query.filter(Company.funding_amount <= funding_max)
    
    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Company.name.ilike(search_term),
                Lead.main_contact_email.ilike(search_term)
            )
        )
    
    # Apply sorting
    if sort_by == "score":
        if sort_order == "desc":
            query = query.order_by(Lead.score.desc())
        else:
            query = query.order_by(Lead.score.asc())
    elif sort_by == "company_name":
        if sort_order == "desc":
            query = query.order_by(Company.name.desc())
        else:
            query = query.order_by(Company.name.asc())
    elif sort_by == "funding":
        if sort_order == "desc":
            query = query.order_by(Company.funding_amount.desc().nulls_last())
        else:
            query = query.order_by(Company.funding_amount.asc().nulls_last())
    else:
        # Default to score desc
        query = query.order_by(Lead.score.desc())
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply pagination
    leads = query.offset(skip).limit(limit).all()
    
    # Build response with company data
    leads_with_companies = []
    for lead in leads:
        company = db.query(Company).filter(Company.id == lead.company_id).first()
        lead_dict = {
            "id": lead.id,
            "company_id": lead.company_id,
            "main_contact_email": lead.main_contact_email,
            "score": lead.score,
            "enrichment_status": lead.enrichment_status,
            "company": {
                "name": company.name,
                "industry": company.industry,
                "location": company.location,
                "funding_amount": company.funding_amount
            } if company else None
        }
        leads_with_companies.append(lead_dict)
    
    return {
        "leads": leads_with_companies,
        "pagination": {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "has_next": (skip + limit) < total_count,
            "has_prev": skip > 0
        },
        "filters_applied": {
            "score_range": [score_min, score_max],
            "enrichment_status": enrichment_status,
            "has_email": has_email,
            "industry": industry,
            "location": location,
            "funding_range": [funding_min, funding_max],
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    }


@router.get("/{lead_id}", response_model=dict)
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific lead by ID with full company and enrichment details"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )
    
    # Get company details
    company = db.query(Company).filter(Company.id == lead.company_id).first()
    
    # Get enrichment data if available
    from app.models.lead_enrichment import LeadEnrichment
    enrichment = db.query(LeadEnrichment).filter(
        LeadEnrichment.lead_id == lead_id
    ).first()
    
    return {
        "lead": {
            "id": lead.id,
            "company_id": lead.company_id,
            "main_contact_email": lead.main_contact_email,
            "score": lead.score,
            "enrichment_status": lead.enrichment_status
        },
        "company": {
            "id": company.id,
            "name": company.name,
            "industry": company.industry,
            "location": company.location,
            "funding_amount": company.funding_amount,
            "updated_at": company.updated_at
        } if company else None,
        "enrichment_data": enrichment.enriched_data if enrichment else None
    }


@router.get("/search/advanced")
async def advanced_lead_search(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    # Multiple value filters
    industries: Optional[str] = Query(None, description="Comma-separated list of industries"),
    locations: Optional[str] = Query(None, description="Comma-separated list of locations"),
    enrichment_statuses: Optional[str] = Query(None, description="Comma-separated enrichment statuses"),
    # Range filters
    score_range: Optional[str] = Query(None, description="Score range as 'min,max'"),
    funding_range: Optional[str] = Query(None, description="Funding range as 'min,max'"),
    # Pagination and sorting
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("score"),
    sort_order: str = Query("desc")
):
    """
    Advanced search with multiple value filters and range queries.
    Supports comma-separated values for multi-select filters.
    """
    query = db.query(Lead).join(Company, Lead.company_id == Company.id)
    
    # Handle multiple industries
    if industries:
        industry_list = [i.strip() for i in industries.split(",")]
        industry_filters = [Company.industry.ilike(f"%{industry}%") for industry in industry_list]
        query = query.filter(or_(*industry_filters))
    
    # Handle multiple locations  
    if locations:
        location_list = [l.strip() for l in locations.split(",")]
        location_filters = [Company.location.ilike(f"%{location}%") for location in location_list]
        query = query.filter(or_(*location_filters))
    
    # Handle multiple enrichment statuses
    if enrichment_statuses:
        status_list = [s.strip() for s in enrichment_statuses.split(",")]
        query = query.filter(Lead.enrichment_status.in_(status_list))
    
    # Handle score range
    if score_range:
        try:
            score_min, score_max = map(float, score_range.split(","))
            query = query.filter(and_(Lead.score >= score_min, Lead.score <= score_max))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid score_range format. Use 'min,max'"
            )
    
    # Handle funding range
    if funding_range:
        try:
            funding_min, funding_max = map(float, funding_range.split(","))
            query = query.filter(and_(
                Company.funding_amount >= funding_min,
                Company.funding_amount <= funding_max
            ))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid funding_range format. Use 'min,max'"
            )
    
    # Apply sorting
    if sort_by == "score":
        query = query.order_by(Lead.score.desc() if sort_order == "desc" else Lead.score.asc())
    elif sort_by == "funding":
        query = query.order_by(
            Company.funding_amount.desc().nulls_last() if sort_order == "desc" 
            else Company.funding_amount.asc().nulls_last()
        )
    
    # Get results
    total_count = query.count()
    leads = query.offset(skip).limit(limit).all()
    
    # Format response
    results = []
    for lead in leads:
        company = db.query(Company).filter(Company.id == lead.company_id).first()
        results.append({
            "id": lead.id,
            "score": lead.score,
            "enrichment_status": lead.enrichment_status,
            "main_contact_email": lead.main_contact_email,
            "company": {
                "name": company.name,
                "industry": company.industry,
                "location": company.location,
                "funding_amount": company.funding_amount
            } if company else None
        })
    
    return {
        "results": results,
        "total": total_count,
        "pagination": {"skip": skip, "limit": limit},
        "filters": {
            "industries": industries,
            "locations": locations,
            "enrichment_statuses": enrichment_statuses,
            "score_range": score_range,
            "funding_range": funding_range
        }
    }