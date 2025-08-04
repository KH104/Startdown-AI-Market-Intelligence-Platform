"""
Notification service for managing subscriptions and sending notifications
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.notification import NotificationSubscription, NotificationLog
from app.models.user import User
from app.models.lead import Lead
from app.models.company import Company


class NotificationService:
    """Service class for notification operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_subscription(
        self,
        user_id: int,
        subscription_type: str,
        filter_criteria: Optional[Dict[str, Any]] = None,
        email_enabled: bool = True,
        webhook_url: Optional[str] = None
    ) -> NotificationSubscription:
        """Create a new notification subscription"""
        subscription = NotificationSubscription(
            user_id=user_id,
            subscription_type=subscription_type,
            filter_criteria=filter_criteria,
            email_enabled=email_enabled,
            webhook_url=webhook_url
        )
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription
    
    def get_user_subscriptions(self, user_id: int) -> List[NotificationSubscription]:
        """Get all subscriptions for a user"""
        return self.db.query(NotificationSubscription).filter(
            NotificationSubscription.user_id == user_id
        ).all()
    
    def update_subscription(
        self,
        subscription_id: int,
        user_id: int,
        **updates
    ) -> Optional[NotificationSubscription]:
        """Update a subscription (only for the owner)"""
        subscription = self.db.query(NotificationSubscription).filter(
            NotificationSubscription.id == subscription_id,
            NotificationSubscription.user_id == user_id
        ).first()
        
        if not subscription:
            return None
        
        for key, value in updates.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription
    
    def delete_subscription(self, subscription_id: int, user_id: int) -> bool:
        """Delete a subscription (only for the owner)"""
        subscription = self.db.query(NotificationSubscription).filter(
            NotificationSubscription.id == subscription_id,
            NotificationSubscription.user_id == user_id
        ).first()
        
        if not subscription:
            return False
        
        self.db.delete(subscription)
        self.db.commit()
        
        return True
    
    def trigger_notification(
        self,
        subscription: NotificationSubscription,
        title: str,
        message: str,
        related_lead_id: Optional[int] = None,
        related_company_id: Optional[int] = None
    ) -> NotificationLog:
        """Trigger a notification for a subscription"""
        # Create notification log entry
        notification_log = NotificationLog(
            subscription_id=subscription.id,
            notification_type=subscription.subscription_type,
            title=title,
            message=message,
            delivery_method="log",  # For MVP, we just log notifications
            related_lead_id=related_lead_id,
            related_company_id=related_company_id
        )
        
        # Mock notification sending
        try:
            # In a real implementation, you would:
            # - Send email if email_enabled
            # - Call webhook if webhook_url is provided
            # - Send push notification, etc.
            
            # For MVP, we just log the notification
            print(f"📧 NOTIFICATION: {title}")
            print(f"   To: User {subscription.user_id}")
            print(f"   Type: {subscription.subscription_type}")
            print(f"   Message: {message}")
            print(f"   Lead ID: {related_lead_id}, Company ID: {related_company_id}")
            
            notification_log.delivery_status = "sent"
            notification_log.sent_at = datetime.utcnow()
            
        except Exception as e:
            notification_log.delivery_status = "failed"
            notification_log.error_message = str(e)
        
        # Update subscription last triggered time
        subscription.last_triggered = datetime.utcnow()
        
        self.db.add(notification_log)
        self.db.commit()
        self.db.refresh(notification_log)
        
        return notification_log
    
    def notify_lead_update(self, lead_id: int, update_type: str = "enriched"):
        """Notify subscribers about lead updates"""
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return
        
        company = self.db.query(Company).filter(Company.id == lead.company_id).first()
        company_name = company.name if company else "Unknown Company"
        
        # Find relevant subscriptions
        subscriptions = self.db.query(NotificationSubscription).filter(
            NotificationSubscription.subscription_type == "lead_updates",
            NotificationSubscription.is_active == True
        ).all()
        
        for subscription in subscriptions:
            # Check if lead matches subscription filters
            if self._lead_matches_filters(lead, company, subscription.filter_criteria):
                title = f"Lead Updated: {company_name}"
                message = f"Lead #{lead_id} from {company_name} has been {update_type}. Current score: {lead.score}"
                
                self.trigger_notification(
                    subscription,
                    title,
                    message,
                    related_lead_id=lead_id,
                    related_company_id=lead.company_id
                )
    
    def notify_new_lead(self, lead_id: int):
        """Notify subscribers about new high-scoring leads"""
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead or lead.score < 70:  # Only notify for high-scoring leads
            return
        
        company = self.db.query(Company).filter(Company.id == lead.company_id).first()
        company_name = company.name if company else "Unknown Company"
        
        # Find relevant subscriptions
        subscriptions = self.db.query(NotificationSubscription).filter(
            NotificationSubscription.subscription_type == "new_leads",
            NotificationSubscription.is_active == True
        ).all()
        
        for subscription in subscriptions:
            if self._lead_matches_filters(lead, company, subscription.filter_criteria):
                title = f"🎯 High-Quality Lead: {company_name}"
                message = f"New lead #{lead_id} with score {lead.score} from {company_name} in {company.industry if company else 'unknown'} industry"
                
                self.trigger_notification(
                    subscription,
                    title,
                    message,
                    related_lead_id=lead_id,
                    related_company_id=lead.company_id
                )
    
    def notify_company_update(self, company_id: int, update_type: str = "updated"):
        """Notify subscribers about company updates"""
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return
        
        # Find relevant subscriptions
        subscriptions = self.db.query(NotificationSubscription).filter(
            NotificationSubscription.subscription_type == "company_updates",
            NotificationSubscription.is_active == True
        ).all()
        
        for subscription in subscriptions:
            if self._company_matches_filters(company, subscription.filter_criteria):
                title = f"Company Updated: {company.name}"
                message = f"Company {company.name} has been {update_type}. Industry: {company.industry}, Funding: ${company.funding_amount:,.0f}" if company.funding_amount else f"Company {company.name} has been {update_type}."
                
                self.trigger_notification(
                    subscription,
                    title,
                    message,
                    related_company_id=company_id
                )
    
    def _lead_matches_filters(
        self,
        lead: Lead,
        company: Optional[Company],
        filter_criteria: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if a lead matches subscription filter criteria"""
        if not filter_criteria:
            return True
        
        # Check score threshold
        min_score = filter_criteria.get("min_score", 0)
        if lead.score < min_score:
            return False
        
        # Check industry filter
        if company and filter_criteria.get("industries"):
            industries = filter_criteria["industries"]
            if not any(industry.lower() in (company.industry or "").lower() for industry in industries):
                return False
        
        # Check location filter
        if company and filter_criteria.get("locations"):
            locations = filter_criteria["locations"]
            if not any(location.lower() in (company.location or "").lower() for location in locations):
                return False
        
        # Check funding filter
        if company and filter_criteria.get("min_funding"):
            min_funding = filter_criteria["min_funding"]
            if not company.funding_amount or company.funding_amount < min_funding:
                return False
        
        return True
    
    def _company_matches_filters(
        self,
        company: Company,
        filter_criteria: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if a company matches subscription filter criteria"""
        if not filter_criteria:
            return True
        
        # Similar filtering logic as lead matching
        if filter_criteria.get("industries"):
            industries = filter_criteria["industries"]
            if not any(industry.lower() in (company.industry or "").lower() for industry in industries):
                return False
        
        if filter_criteria.get("locations"):
            locations = filter_criteria["locations"]
            if not any(location.lower() in (company.location or "").lower() for location in locations):
                return False
        
        return True
    
    def get_notification_logs(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[NotificationLog]:
        """Get notification logs for a user"""
        # Get user's subscriptions first
        subscription_ids = self.db.query(NotificationSubscription.id).filter(
            NotificationSubscription.user_id == user_id
        ).subquery()
        
        # Get logs for those subscriptions
        logs = self.db.query(NotificationLog).filter(
            NotificationLog.subscription_id.in_(subscription_ids)
        ).order_by(NotificationLog.created_at.desc()).limit(limit).all()
        
        return logs