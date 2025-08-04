"""
Lead model for prospect management and scoring
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Lead(Base):
    """Lead model for managing prospects and opportunities"""
    
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    main_contact_email = Column(String(255), nullable=True)
    score = Column(Float, default=0.0, index=True)
    enrichment_status = Column(String(50), default="pending")  # pending, in_progress, completed, failed
    
    # Relationships
    company = relationship("Company", back_populates="leads")
    enrichments = relationship("LeadEnrichment", back_populates="lead")
    
    def __repr__(self):
        return f"<Lead(id={self.id}, company_id={self.company_id}, score={self.score})>"