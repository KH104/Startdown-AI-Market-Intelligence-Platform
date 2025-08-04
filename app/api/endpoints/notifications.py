"""
Notification subscription endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.services.notification_service import NotificationService
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.notification import NotificationSubscription, NotificationLog
from pydantic import BaseModel

router = APIRouter()


class SubscriptionCreate(BaseModel):
    """Schema for creating notification subscription"""
    subscription_type: str  # lead_updates, company_updates, new_leads
    email_enabled: bool = True
    webhook_url: Optional[str] = None
    filter_criteria: Optional[Dict[str, Any]] = None


class SubscriptionUpdate(BaseModel):
    """Schema for updating notification subscription"""
    is_active: Optional[bool] = None
    email_enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    filter_criteria: Optional[Dict[str, Any]] = None


class SubscriptionResponse(BaseModel):
    """Schema for subscription response"""
    id: int
    subscription_type: str
    is_active: bool
    email_enabled: bool
    webhook_url: Optional[str]
    filter_criteria: Optional[Dict[str, Any]]
    created_at: str
    last_triggered: Optional[str]
    
    class Config:
        from_attributes = True


@router.post("/subscribe", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new notification subscription.
    Subscribe to lead updates, company changes, or new high-quality leads.
    """
    notification_service = NotificationService(db)
    
    # Validate subscription type
    valid_types = ["lead_updates", "company_updates", "new_leads"]
    if subscription_data.subscription_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid subscription type. Must be one of: {valid_types}"
        )
    
    # Check if user already has this subscription type
    existing = db.query(NotificationSubscription).filter(
        NotificationSubscription.user_id == current_user.id,
        NotificationSubscription.subscription_type == subscription_data.subscription_type,
        NotificationSubscription.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Active subscription for {subscription_data.subscription_type} already exists"
        )
    
    # Create subscription
    subscription = notification_service.create_subscription(
        user_id=current_user.id,
        subscription_type=subscription_data.subscription_type,
        filter_criteria=subscription_data.filter_criteria,
        email_enabled=subscription_data.email_enabled,
        webhook_url=subscription_data.webhook_url
    )
    
    return subscription


@router.get("/subscriptions", response_model=List[SubscriptionResponse])
async def get_user_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all notification subscriptions for the current user.
    """
    notification_service = NotificationService(db)
    subscriptions = notification_service.get_user_subscriptions(current_user.id)
    
    return subscriptions


@router.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    update_data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a notification subscription.
    Can modify filters, enable/disable, change delivery methods.
    """
    notification_service = NotificationService(db)
    
    # Update subscription
    subscription = notification_service.update_subscription(
        subscription_id=subscription_id,
        user_id=current_user.id,
        **update_data.dict(exclude_unset=True)
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    return subscription


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a notification subscription.
    Stops all notifications for this subscription.
    """
    notification_service = NotificationService(db)
    
    success = notification_service.delete_subscription(
        subscription_id=subscription_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    return {"message": "Subscription deleted successfully"}


@router.get("/logs")
async def get_notification_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500, description="Number of logs to return")
):
    """
    Get notification logs for the current user.
    Shows history of sent notifications and delivery status.
    """
    notification_service = NotificationService(db)
    logs = notification_service.get_notification_logs(current_user.id, limit)
    
    return {
        "logs": [
            {
                "id": log.id,
                "notification_type": log.notification_type,
                "title": log.title,
                "message": log.message,
                "delivery_method": log.delivery_method,
                "delivery_status": log.delivery_status,
                "error_message": log.error_message,
                "related_lead_id": log.related_lead_id,
                "related_company_id": log.related_company_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None
            } for log in logs
        ],
        "count": len(logs)
    }


@router.post("/test/{subscription_id}")
async def test_notification(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a test notification for a subscription.
    Useful for verifying notification setup.
    """
    notification_service = NotificationService(db)
    
    # Get subscription
    subscription = db.query(NotificationSubscription).filter(
        NotificationSubscription.id == subscription_id,
        NotificationSubscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Send test notification
    notification_log = notification_service.trigger_notification(
        subscription=subscription,
        title="🧪 Test Notification",
        message=f"This is a test notification for your {subscription.subscription_type} subscription. Everything is working correctly!",
        related_lead_id=None,
        related_company_id=None
    )
    
    return {
        "message": "Test notification sent",
        "log_id": notification_log.id,
        "delivery_status": notification_log.delivery_status
    }


@router.get("/types")
async def get_subscription_types():
    """
    Get available notification subscription types and their descriptions.
    """
    return {
        "subscription_types": [
            {
                "type": "lead_updates",
                "name": "Lead Updates",
                "description": "Get notified when leads are enriched, scored, or updated",
                "filter_options": [
                    "min_score: Minimum lead score to trigger notifications",
                    "industries: List of industries to monitor",
                    "locations: List of locations to monitor",
                    "min_funding: Minimum company funding amount"
                ]
            },
            {
                "type": "company_updates", 
                "name": "Company Updates",
                "description": "Get notified when company information is updated",
                "filter_options": [
                    "industries: List of industries to monitor",
                    "locations: List of locations to monitor"
                ]
            },
            {
                "type": "new_leads",
                "name": "New High-Quality Leads",
                "description": "Get notified when new high-scoring leads (70+ score) are discovered",
                "filter_options": [
                    "min_score: Minimum score threshold (default: 70)",
                    "industries: List of industries to monitor",
                    "locations: List of locations to monitor",
                    "min_funding: Minimum company funding amount"
                ]
            }
        ]
    }