"""
Lead enrichment model for tracking data enhancement
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class LeadEnrichment(Base):
    """Lead enrichment model for tracking enriched data"""
    
    __tablename__ = "lead_enrichments"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    enriched_data = Column(JSON, nullable=True)  # Stores enriched data as JSON
    last_checked = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    lead = relationship("Lead", back_populates="enrichments")
    
    def __repr__(self):
        return f"<LeadEnrichment(id={self.id}, lead_id={self.lead_id}, last_checked={self.last_checked})>"