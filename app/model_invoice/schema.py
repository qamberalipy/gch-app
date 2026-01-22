# app/model_invoice/schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

# --- New Helper Schema ---
class UserBasicInfo(BaseModel):
    id: int
    username: Optional[str]
    full_name: Optional[str]
    profile_picture_url: Optional[str]

    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    invoice_date: date
    subscription: float = 0.0
    tips: float = 0.0
    posts: float = 0.0
    messages: float = 0.0
    referrals: float = 0.0
    streams: float = 0.0
    others: float = 0.0

class InvoiceCreate(InvoiceBase):
    user_id: int

class InvoiceUpdate(BaseModel):
    invoice_date: Optional[date] = None
    subscription: Optional[float] = None
    tips: Optional[float] = None
    posts: Optional[float] = None
    messages: Optional[float] = None
    referrals: Optional[float] = None
    streams: Optional[float] = None
    others: Optional[float] = None

class InvoiceResponse(InvoiceBase):
    id: int
    user_id: int
    total_earnings: float
    
    # --- ADD THIS FIELD ---
    user: Optional[UserBasicInfo] = None 
    
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True