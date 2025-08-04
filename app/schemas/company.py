"""
Company schemas for API request/response validation
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CompanyBase(BaseModel):
    """Base company schema"""
    name: str
    industry: Optional[str] = None
    location: Optional[str] = None
    funding_amount: Optional[float] = None


class CompanyCreate(CompanyBase):
    """Schema for company creation"""
    pass


class CompanyUpdate(BaseModel):
    """Schema for company updates"""
    name: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    funding_amount: Optional[float] = None


class CompanyResponse(CompanyBase):
    """Schema for company response"""
    id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CompanyBatch(BaseModel):
    """Schema for batch company ingestion"""
    companies: list[CompanyCreate]