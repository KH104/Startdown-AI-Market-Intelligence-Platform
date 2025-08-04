"""
Lead scoring endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.services.scoring_service import ScoringService
from app.services.advanced_scoring_service import AdvancedScoringService
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.lead import Lead
from pydantic import BaseModel

router = APIRouter()


class ScoringCriteria(BaseModel):
    """Schema for scoring criteria"""
    target_industries: Optional[List[str]] = None
    target_locations: Optional[List[str]] = None
    min_funding: Optional[float] = None
    max_funding: Optional[float] = None


class ScoreLeadRequest(BaseModel):
    """Request schema for lead scoring"""
    lead_id: int
    scoring_criteria: Optional[ScoringCriteria] = None


class ScoreBatchRequest(BaseModel):
    """Request schema for batch lead scoring"""
    lead_ids: List[int]
    scoring_criteria: Optional[ScoringCriteria] = None


@router.post("/lead/{lead_id}")
async def score_single_lead(
    lead_id: int,
    scoring_criteria: Optional[ScoringCriteria] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate and update the score for a single lead.
    Score is based on industry, location, funding, and data completeness.
    """
    scoring_service = ScoringService(db)
    
    # Check if lead exists
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Convert criteria to dict if provided
    criteria_dict = None
    if scoring_criteria:
        criteria_dict = scoring_criteria.dict(exclude_unset=True)
    
    # Score the lead
    score = scoring_service.score_lead_by_id(lead_id, criteria_dict)
    
    if score is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to score lead"
        )
    
    return {
        "lead_id": lead_id,
        "score": score,
        "status": "completed",
        "criteria_used": criteria_dict or scoring_service.get_default_scoring_criteria()
    }


@router.post("/batch")
async def score_leads_batch(
    request: ScoreBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Score multiple leads in batch using the same criteria.
    Returns summary of successes and failures with individual scores.
    """
    scoring_service = ScoringService(db)
    
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
    
    # Convert criteria to dict if provided
    criteria_dict = None
    if request.scoring_criteria:
        criteria_dict = request.scoring_criteria.dict(exclude_unset=True)
    
    # Score leads
    results = scoring_service.score_leads_batch(request.lead_ids, criteria_dict)
    
    return {
        "total_requested": len(request.lead_ids),
        "scored": results["scored"],
        "failed": results["failed"],
        "errors": results["errors"],
        "scores": results["scores"],
        "criteria_used": criteria_dict or scoring_service.get_default_scoring_criteria()
    }


@router.post("/rescore-all")
async def rescore_all_leads(
    scoring_criteria: Optional[ScoringCriteria] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rescore all leads in the database using new criteria.
    Useful when scoring logic changes or criteria are updated.
    """
    scoring_service = ScoringService(db)
    
    # Convert criteria to dict if provided
    criteria_dict = None
    if scoring_criteria:
        criteria_dict = scoring_criteria.dict(exclude_unset=True)
    
    # Rescore all leads
    results = scoring_service.rescore_all_leads(criteria_dict)
    
    return {
        "message": "Rescored all leads",
        "total_leads": results["scored"] + results["failed"],
        "scored": results["scored"],
        "failed": results["failed"],
        "errors": results["errors"],
        "criteria_used": criteria_dict or scoring_service.get_default_scoring_criteria()
    }


@router.get("/criteria/default")
async def get_default_criteria(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the default scoring criteria used by the system.
    Useful for understanding how leads are scored.
    """
    scoring_service = ScoringService(db)
    default_criteria = scoring_service.get_default_scoring_criteria()
    
    return {
        "default_criteria": default_criteria,
        "description": {
            "industry_weight": "30 points (out of 100)",
            "location_weight": "20 points (out of 100)",
            "funding_weight": "25 points (out of 100)",
            "company_size_weight": "15 points (out of 100)",
            "data_completeness_weight": "10 points (out of 100)"
        }
    }


@router.get("/top-leads")
async def get_top_scoring_leads(
    limit: int = 50,
    min_score: float = 0.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the highest scoring leads for quick access to best prospects.
    Returns leads sorted by score in descending order.
    """
    top_leads = db.query(Lead).filter(
        Lead.score >= min_score
    ).order_by(Lead.score.desc()).limit(limit).all()
    
    return {
        "top_leads": [
            {
                "id": lead.id,
                "company_id": lead.company_id,
                "score": lead.score,
                "main_contact_email": lead.main_contact_email,
                "enrichment_status": lead.enrichment_status
            } for lead in top_leads
        ],
        "count": len(top_leads),
        "filters": {
            "min_score": min_score,
            "limit": limit
        }
    }