# app/model_invoice/schema.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

# --- Helper Schema for User ---
class UserBasicInfo(BaseModel):
    id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    profile_picture_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

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
    user: Optional[UserBasicInfo] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Pagination Schema ---
class InvoicePaginatedResponse(BaseModel):
    items: List[InvoiceResponse]
    total: int
    page: int
    size: int