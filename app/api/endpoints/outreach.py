"""
Outreach endpoints for email campaigns and communications
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.services.outreach_service import OutreachService
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.outreach import OutreachCampaign, OutreachAttempt
from pydantic import BaseModel, EmailStr

router = APIRouter()


class CampaignCreate(BaseModel):
    """Schema for creating outreach campaign"""
    name: str
    subject_template: str
    message_template: str
    auto_send: bool = False


class CampaignResponse(BaseModel):
    """Schema for campaign response"""
    id: int
    name: str
    subject_template: str
    message_template: str
    is_active: bool
    auto_send: bool
    total_sent: int
    total_opened: int
    total_replied: int
    created_at: str
    
    class Config:
        from_attributes = True


class OutreachRequest(BaseModel):
    """Schema for single outreach request"""
    lead_id: int
    subject: str
    message: str
    campaign_id: Optional[int] = None
    delivery_method: str = "email"


class BulkOutreachRequest(BaseModel):
    """Schema for bulk outreach request"""
    lead_ids: List[int]
    campaign_id: Optional[int] = None
    subject_template: Optional[str] = None
    message_template: Optional[str] = None


class OutreachAttemptResponse(BaseModel):
    """Schema for outreach attempt response"""
    id: int
    lead_id: int
    recipient_email: str
    subject: str
    status: str
    delivery_method: str
    created_at: str
    sent_at: Optional[str]
    opened_at: Optional[str]
    replied_at: Optional[str]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new outreach campaign with email templates.
    Campaigns allow you to organize and track email outreach efforts.
    """
    outreach_service = OutreachService(db)
    
    campaign = outreach_service.create_campaign(
        user_id=current_user.id,
        name=campaign_data.name,
        subject_template=campaign_data.subject_template,
        message_template=campaign_data.message_template,
        auto_send=campaign_data.auto_send
    )
    
    return campaign


@router.get("/campaigns", response_model=List[CampaignResponse])
async def get_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all outreach campaigns for the current user.
    """
    outreach_service = OutreachService(db)
    campaigns = outreach_service.get_user_campaigns(current_user.id)
    
    return campaigns


@router.post("/send", status_code=status.HTTP_201_CREATED)
async def send_outreach(
    request: OutreachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send outreach email to a single lead.
    Tracks delivery status and logs the attempt.
    """
    outreach_service = OutreachService(db)
    
    try:
        attempt = outreach_service.send_outreach(
            lead_id=request.lead_id,
            user_id=current_user.id,
            subject=request.subject,
            message=request.message,
            campaign_id=request.campaign_id,
            delivery_method=request.delivery_method
        )
        
        return {
            "message": "Outreach sent successfully",
            "attempt_id": attempt.id,
            "status": attempt.status,
            "recipient": attempt.recipient_email
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send outreach: {str(e)}"
        )


@router.post("/send/bulk")
async def send_bulk_outreach(
    request: BulkOutreachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send outreach to multiple leads using campaign templates.
    Personalizes messages for each lead automatically.
    """
    outreach_service = OutreachService(db)
    
    if not request.lead_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No lead IDs provided"
        )
    
    try:
        results = outreach_service.send_bulk_outreach(
            lead_ids=request.lead_ids,
            user_id=current_user.id,
            campaign_id=request.campaign_id,
            subject_template=request.subject_template,
            message_template=request.message_template
        )
        
        return {
            "message": f"Bulk outreach completed",
            "total_leads": len(request.lead_ids),
            "sent": results["sent"],
            "failed": results["failed"],
            "errors": results["errors"],
            "attempt_ids": results["attempts"]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk outreach: {str(e)}"
        )


@router.get("/attempts")
async def get_outreach_attempts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    campaign_id: Optional[int] = Query(None, description="Filter by campaign ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of attempts to return")
):
    """
    Get outreach attempts for the current user.
    Shows history of sent emails and their delivery status.
    """
    outreach_service = OutreachService(db)
    attempts = outreach_service.get_outreach_attempts(
        user_id=current_user.id,
        lead_id=lead_id,
        campaign_id=campaign_id,
        limit=limit
    )
    
    # Filter by status if provided
    if status:
        attempts = [attempt for attempt in attempts if attempt.status == status]
    
    return {
        "attempts": [
            {
                "id": attempt.id,
                "lead_id": attempt.lead_id,
                "campaign_id": attempt.campaign_id,
                "recipient_email": attempt.recipient_email,
                "subject": attempt.subject,
                "status": attempt.status,
                "delivery_method": attempt.delivery_method,
                "created_at": attempt.created_at.isoformat() if attempt.created_at else None,
                "sent_at": attempt.sent_at.isoformat() if attempt.sent_at else None,
                "opened_at": attempt.opened_at.isoformat() if attempt.opened_at else None,
                "replied_at": attempt.replied_at.isoformat() if attempt.replied_at else None,
                "error_message": attempt.error_message
            } for attempt in attempts
        ],
        "count": len(attempts),
        "filters": {
            "lead_id": lead_id,
            "campaign_id": campaign_id,
            "status": status
        }
    }


@router.get("/templates")
async def get_email_templates():
    """
    Get default email templates for different outreach scenarios.
    Templates support personalization variables.
    """
    outreach_service = OutreachService(None)  # No DB needed for templates
    templates = outreach_service.get_default_templates()
    
    return {
        "templates": templates,
        "personalization_variables": [
            "{company_name} - Company name",
            "{company_industry} - Company industry",
            "{company_location} - Company location",
            "{company_funding} - Company funding amount",
            "{contact_name} - Contact name (extracted from email)",
            "{contact_email} - Contact email address",
            "{job_title} - Contact job title (from enrichment)",
            "{linkedin_url} - Contact LinkedIn URL",
            "{tech_stack} - Company technology stack",
            "{lead_score} - Lead quality score"
        ]
    }


@router.post("/attempts/{attempt_id}/opened")
async def mark_opened(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark an outreach attempt as opened.
    Used for tracking email open rates.
    """
    outreach_service = OutreachService(db)
    
    success = outreach_service.mark_opened(attempt_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outreach attempt not found"
        )
    
    return {"message": "Outreach marked as opened"}


@router.post("/attempts/{attempt_id}/replied")
async def mark_replied(
    attempt_id: int,
    reply_content: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark an outreach attempt as replied with response content.
    Used for tracking reply rates and responses.
    """
    outreach_service = OutreachService(db)
    
    success = outreach_service.mark_replied(attempt_id, current_user.id, reply_content)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outreach attempt not found"
        )
    
    return {"message": "Outreach marked as replied"}


@router.get("/stats")
async def get_outreach_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    campaign_id: Optional[int] = Query(None, description="Get stats for specific campaign")
):
    """
    Get outreach statistics and performance metrics.
    """
    outreach_service = OutreachService(db)
    
    # Get attempts for analysis
    attempts = outreach_service.get_outreach_attempts(
        user_id=current_user.id,
        campaign_id=campaign_id,
        limit=10000  # Get all for stats
    )
    
    # Calculate statistics
    total_attempts = len(attempts)
    sent = len([a for a in attempts if a.status == "sent"])
    opened = len([a for a in attempts if a.opened_at is not None])
    replied = len([a for a in attempts if a.replied_at is not None])
    failed = len([a for a in attempts if a.status == "failed"])
    
    open_rate = (opened / sent * 100) if sent > 0 else 0
    reply_rate = (replied / sent * 100) if sent > 0 else 0
    success_rate = (sent / total_attempts * 100) if total_attempts > 0 else 0
    
    return {
        "stats": {
            "total_attempts": total_attempts,
            "sent": sent,
            "opened": opened,
            "replied": replied,
            "failed": failed,
            "open_rate": round(open_rate, 2),
            "reply_rate": round(reply_rate, 2),
            "success_rate": round(success_rate, 2)
        },
        "campaign_id": campaign_id,
        "recent_attempts": [
            {
                "id": attempt.id,
                "lead_id": attempt.lead_id,
                "recipient": attempt.recipient_email,
                "status": attempt.status,
                "sent_at": attempt.sent_at.isoformat() if attempt.sent_at else None
            } for attempt in attempts[:10]  # Last 10 attempts
        ]
    }