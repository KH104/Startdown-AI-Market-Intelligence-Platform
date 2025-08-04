"""
Outreach model for tracking email campaigns and communications
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class OutreachCampaign(Base):
    """Outreach campaign model"""
    
    __tablename__ = "outreach_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Campaign details
    name = Column(String(200), nullable=False)
    subject_template = Column(String(300), nullable=False)
    message_template = Column(Text, nullable=False)
    
    # Campaign settings
    is_active = Column(Boolean, default=True)
    auto_send = Column(Boolean, default=False)
    
    # Statistics
    total_sent = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_replied = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # user = relationship("User")
    
    def __repr__(self):
        return f"<OutreachCampaign(id={self.id}, name={self.name}, user_id={self.user_id})>"


class OutreachAttempt(Base):
    """Individual outreach attempt model"""
    
    __tablename__ = "outreach_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("outreach_campaigns.id"), nullable=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Email details
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    
    # Delivery tracking
    status = Column(String(50), default="pending")  # pending, sent, failed, opened, replied
    delivery_method = Column(String(50), default="email")  # email, linkedin, phone
    
    # Response tracking
    opened_at = Column(DateTime(timezone=True), nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    reply_content = Column(Text, nullable=True)
    
    # Error tracking
    error_message = Column(String(500), nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # campaign = relationship("OutreachCampaign")
    # lead = relationship("Lead")
    # user = relationship("User")
    
    def __repr__(self):
        return f"<OutreachAttempt(id={self.id}, lead_id={self.lead_id}, status={self.status})>"