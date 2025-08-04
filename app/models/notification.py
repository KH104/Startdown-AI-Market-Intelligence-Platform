"""
Notification subscription model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class NotificationSubscription(Base):
    """Notification subscription model"""
    
    __tablename__ = "notification_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Subscription settings
    subscription_type = Column(String(50), nullable=False)  # lead_updates, company_updates, new_leads
    is_active = Column(Boolean, default=True)
    
    # Notification preferences
    email_enabled = Column(Boolean, default=True)
    webhook_url = Column(String(500), nullable=True)
    
    # Filter criteria (JSON field for flexibility)
    filter_criteria = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # user = relationship("User")
    
    def __repr__(self):
        return f"<NotificationSubscription(id={self.id}, type={self.subscription_type}, user_id={self.user_id})>"


class NotificationLog(Base):
    """Notification log for tracking sent notifications"""
    
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("notification_subscriptions.id"), nullable=False)
    
    # Notification details
    notification_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(String(1000), nullable=False)
    
    # Delivery details
    delivery_method = Column(String(20), nullable=False)  # email, webhook, log
    delivery_status = Column(String(20), default="pending")  # pending, sent, failed
    error_message = Column(String(500), nullable=True)
    
    # Related entity information
    related_lead_id = Column(Integer, nullable=True)
    related_company_id = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, type={self.notification_type}, status={self.delivery_status})>"