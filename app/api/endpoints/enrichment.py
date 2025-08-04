"""
Lead enrichment endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.services.enrichment_service import EnrichmentService
from app.services.enhanced_enrichment_service import EnhancedEnrichmentService
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.lead import Lead
from pydantic import BaseModel

router = APIRouter()


class EnrichLeadRequest(BaseModel):
    """Request schema for lead enrichment"""
    lead_id: int


class EnrichBatchRequest(BaseModel):
    """Request schema for batch lead enrichment"""
    lead_ids: List[int]


@router.post("/lead/{lead_id}")
async def enrich_single_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enrich a single lead with missing information using AI and mock data.
    Fills in contact email, phone, LinkedIn, and other relevant data.
    """
    enrichment_service = EnrichmentService(db)
    
    # Check if lead exists
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Enrich the lead
    enriched_lead = enrichment_service.enrich_lead(lead_id)
    
    if not enriched_lead:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enrich lead"
        )
    
    # Get enrichment data
    enrichment_data = enrichment_service.get_enrichment_data(lead_id)
    
    return {
        "lead_id": lead_id,
        "status": "completed",
        "enriched_data": enrichment_data,
        "lead": {
            "id": enriched_lead.id,
            "company_id": enriched_lead.company_id,
            "main_contact_email": enriched_lead.main_contact_email,
            "score": enriched_lead.score,
            "enrichment_status": enriched_lead.enrichment_status
        }
    }


@router.post("/batch")
async def enrich_leads_batch(
    request: EnrichBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enrich multiple leads in batch.
    Processes each lead and returns summary of successes and failures.
    """
    enrichment_service = EnrichmentService(db)
    
    if not request.lead_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No lead IDs provided"
        )
    
    # Validate that all leads exist
    existing_leads = db.query(Lead).filter(Lead.id.in_(request.lead_ids)).all()
    existing_ids = {lead.id for lead in existing_leads}
    missing_ids = set(request.lead_ids) - existing_ids
    
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leads not found: {list(missing_ids)}"
        )
    
    # Enrich leads
    results = enrichment_service.enrich_leads_batch(request.lead_ids)
    
    return {
        "total_requested": len(request.lead_ids),
        "enriched": results["enriched"],
        "failed": results["failed"],
        "errors": results["errors"],
        "status": "completed"
    }


@router.get("/pending")
async def get_pending_leads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 100
):
    """
    Get leads that are pending enrichment.
    Returns leads with enrichment_status = 'pending'.
    """
    pending_leads = db.query(Lead).filter(
        Lead.enrichment_status == "pending"
    ).limit(limit).all()
    
    return {
        "pending_leads": [
            {
                "id": lead.id,
                "company_id": lead.company_id,
                "main_contact_email": lead.main_contact_email,
                "enrichment_status": lead.enrichment_status
            } for lead in pending_leads
        ],
        "count": len(pending_leads)
    }


@router.post("/auto-enrich")
async def auto_enrich_pending(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """
    Automatically enrich all pending leads up to the specified limit.
    Useful for batch processing and automation.
    """
    # Get pending leads
    pending_leads = db.query(Lead).filter(
        Lead.enrichment_status == "pending"
    ).limit(limit).all()
    
    if not pending_leads:
        return {
            "message": "No pending leads found",
            "enriched": 0
        }
    
    # Enrich them
    enrichment_service = EnrichmentService(db)
    lead_ids = [lead.id for lead in pending_leads]
    results = enrichment_service.enrich_leads_batch(lead_ids)
    
    return {
        "message": f"Auto-enriched {results['enriched']} leads",
        "total_processed": len(lead_ids),
        "enriched": results["enriched"],
        "failed": results["failed"],
        "errors": results["errors"]
    }


@router.get("/lead/{lead_id}/data")
async def get_enrichment_data(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get enrichment data for a specific lead.
    Returns the detailed enrichment information if available.
    """
    enrichment_service = EnrichmentService(db)
    
    # Check if lead exists
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    enrichment_data = enrichment_service.get_enrichment_data(lead_id)
    
    if not enrichment_data:
        return {
            "lead_id": lead_id,
            "enriched": False,
            "message": "No enrichment data available"
        }
    
    return {
        "lead_id": lead_id,
        "enriched": True,
        "data": enrichment_data
    }