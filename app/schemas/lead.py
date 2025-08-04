"""
Lead schemas for API request/response validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class LeadBase(BaseModel):
    """Base lead schema"""
    company_id: int
    main_contact_email: Optional[EmailStr] = None
    score: Optional[float] = 0.0
    enrichment_status: Optional[str] = "pending"


class LeadCreate(LeadBase):
    """Schema for lead creation"""
    pass


class LeadUpdate(BaseModel):
    """Schema for lead updates"""
    main_contact_email: Optional[EmailStr] = None
    score: Optional[float] = None
    enrichment_status: Optional[str] = None


class LeadResponse(LeadBase):
    """Schema for lead response"""
    id: int
    
    class Config:
        from_attributes = True


class LeadBatch(BaseModel):
    """Schema for batch lead ingestion"""
    leads: list[LeadCreate]


class LeadWithCompany(LeadResponse):
    """Schema for lead with company information"""
    company: Optional[dict] = None