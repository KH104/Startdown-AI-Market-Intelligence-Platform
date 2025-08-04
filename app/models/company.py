"""
Company model for business data and market intelligence
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Company(Base):
    """Company model for business intelligence and lead generation"""
    
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False, index=True)
    industry = Column(String(100), nullable=True, index=True)
    location = Column(String(200), nullable=True, index=True)
    funding_amount = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    leads = relationship("Lead", back_populates="company")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name}, industry={self.industry})>"