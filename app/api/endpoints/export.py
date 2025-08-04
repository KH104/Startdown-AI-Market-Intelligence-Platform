"""
Export endpoints for downloading lead data
"""
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from app.database import get_db
from app.models.lead import Lead
from app.models.company import Company
from app.models.lead_enrichment import LeadEnrichment
from app.auth.dependencies import get_current_user
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()


class ExportRequest(BaseModel):
    """Request schema for lead export"""
    lead_ids: Optional[List[int]] = None
    # Filter parameters
    score_min: Optional[float] = None
    score_max: Optional[float] = None
    enrichment_status: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    funding_min: Optional[float] = None
    funding_max: Optional[float] = None
    search: Optional[str] = None
    # Export options
    include_enrichment_data: bool = False
    max_records: int = 10000


@router.post("/leads/csv")
async def export_leads_csv(
    request: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export filtered leads to CSV format.
    Returns a downloadable CSV file with lead and company data.
    """
    # Build query based on filters or specific lead IDs
    if request.lead_ids:
        # Export specific leads
        query = db.query(Lead).filter(Lead.id.in_(request.lead_ids))
    else:
        # Export filtered leads
        query = db.query(Lead).join(Company, Lead.company_id == Company.id)
        
        # Apply filters (same logic as search endpoint)
        if request.score_min is not None:
            query = query.filter(Lead.score >= request.score_min)
        
        if request.score_max is not None:
            query = query.filter(Lead.score <= request.score_max)
        
        if request.enrichment_status:
            query = query.filter(Lead.enrichment_status == request.enrichment_status)
        
        if request.industry:
            query = query.filter(Company.industry.ilike(f"%{request.industry}%"))
        
        if request.location:
            query = query.filter(Company.location.ilike(f"%{request.location}%"))
        
        if request.funding_min is not None:
            query = query.filter(Company.funding_amount >= request.funding_min)
        
        if request.funding_max is not None:
            query = query.filter(Company.funding_amount <= request.funding_max)
        
        if request.search:
            search_term = f"%{request.search}%"
            query = query.filter(
                or_(
                    Company.name.ilike(search_term),
                    Lead.main_contact_email.ilike(search_term)
                )
            )
    
    # Limit results to prevent large exports
    query = query.limit(request.max_records)
    leads = query.all()
    
    if not leads:
        raise HTTPException(
            status_code=404,
            detail="No leads found matching the criteria"
        )
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Define CSV headers
    headers = [
        "Lead ID",
        "Company Name",
        "Industry",
        "Location",
        "Funding Amount",
        "Contact Email",
        "Lead Score",
        "Enrichment Status"
    ]
    
    if request.include_enrichment_data:
        headers.extend([
            "Contact Phone",
            "Contact LinkedIn",
            "Job Title",
            "Company Insights",
            "Market Intelligence"
        ])
    
    writer.writerow(headers)
    
    # Write lead data
    for lead in leads:
        # Get company data
        company = db.query(Company).filter(Company.id == lead.company_id).first()
        
        # Basic row data
        row = [
            lead.id,
            company.name if company else "",
            company.industry if company else "",
            company.location if company else "",
            company.funding_amount if company else "",
            lead.main_contact_email or "",
            lead.score,
            lead.enrichment_status
        ]
        
        # Add enrichment data if requested
        if request.include_enrichment_data:
            enrichment = db.query(LeadEnrichment).filter(
                LeadEnrichment.lead_id == lead.id
            ).first()
            
            if enrichment and enrichment.enriched_data:
                data = enrichment.enriched_data
                contact_info = data.get("contact_info", {})
                company_insights = data.get("company_insights", {})
                market_intel = data.get("market_intelligence", {})
                
                row.extend([
                    contact_info.get("phone", ""),
                    contact_info.get("linkedin", ""),
                    contact_info.get("job_title", ""),
                    str(company_insights),
                    str(market_intel)
                ])
            else:
                row.extend(["", "", "", "", ""])
        
        writer.writerow(row)
    
    # Prepare response
    csv_content = output.getvalue()
    output.close()
    
    # Generate filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"leads_export_{timestamp}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/leads/csv")
async def export_leads_csv_get(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    # Filter parameters
    score_min: Optional[float] = Query(None, ge=0, le=100),
    score_max: Optional[float] = Query(None, ge=0, le=100),
    enrichment_status: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    funding_min: Optional[float] = Query(None, ge=0),
    funding_max: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None),
    include_enrichment: bool = Query(False, description="Include enrichment data columns"),
    max_records: int = Query(1000, ge=1, le=10000, description="Maximum records to export")
):
    """
    Export leads to CSV using GET parameters.
    Convenient for direct browser downloads with URL parameters.
    """
    # Create export request from query parameters
    export_request = ExportRequest(
        score_min=score_min,
        score_max=score_max,
        enrichment_status=enrichment_status,
        industry=industry,
        location=location,
        funding_min=funding_min,
        funding_max=funding_max,
        search=search,
        include_enrichment_data=include_enrichment,
        max_records=max_records
    )
    
    # Use the same export logic
    return await export_leads_csv(export_request, db, current_user)


@router.get("/leads/preview")
async def preview_export(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    # Filter parameters
    score_min: Optional[float] = Query(None, ge=0, le=100),
    score_max: Optional[float] = Query(None, ge=0, le=100),
    enrichment_status: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    funding_min: Optional[float] = Query(None, ge=0),
    funding_max: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None)
):
    """
    Preview what would be exported without actually generating the CSV.
    Returns count and sample of leads that match the export criteria.
    """
    # Build the same query as export
    query = db.query(Lead).join(Company, Lead.company_id == Company.id)
    
    # Apply filters
    if score_min is not None:
        query = query.filter(Lead.score >= score_min)
    
    if score_max is not None:
        query = query.filter(Lead.score <= score_max)
    
    if enrichment_status:
        query = query.filter(Lead.enrichment_status == enrichment_status)
    
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))
    
    if location:
        query = query.filter(Company.location.ilike(f"%{location}%"))
    
    if funding_min is not None:
        query = query.filter(Company.funding_amount >= funding_min)
    
    if funding_max is not None:
        query = query.filter(Company.funding_amount <= funding_max)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Company.name.ilike(search_term),
                Lead.main_contact_email.ilike(search_term)
            )
        )
    
    # Get total count
    total_count = query.count()
    
    # Get sample of first 10 records
    sample_leads = query.limit(10).all()
    
    # Format sample data
    sample_data = []
    for lead in sample_leads:
        company = db.query(Company).filter(Company.id == lead.company_id).first()
        sample_data.append({
            "lead_id": lead.id,
            "company_name": company.name if company else "",
            "industry": company.industry if company else "",
            "location": company.location if company else "",
            "funding_amount": company.funding_amount if company else None,
            "contact_email": lead.main_contact_email,
            "score": lead.score,
            "enrichment_status": lead.enrichment_status
        })
    
    return {
        "total_count": total_count,
        "sample_data": sample_data,
        "filters_applied": {
            "score_range": [score_min, score_max],
            "enrichment_status": enrichment_status,
            "industry": industry,
            "location": location,
            "funding_range": [funding_min, funding_max],
            "search": search
        },
        "export_ready": total_count > 0
    }