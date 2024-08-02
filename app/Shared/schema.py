from pydantic import BaseModel
import datetime
from datetime import date
from typing import Optional, List, Any

class User(BaseModel):
    first_name: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    user_type: str

class CoachBase(BaseModel):
    wallet_address: Optional[str] = None 
    org_id: Optional[int] = None
    coach_status: Optional[str] = "pending"
    own_coach_id: Optional[str] = None
    profile_img: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[datetime.date] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    mobile_number: Optional[str] = None
    notes: Optional[str] = None
    source_id: Optional[int] = None
    country_id: Optional[int] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    check_in: Optional[datetime.datetime] = None
    last_online: Optional[datetime.datetime] = None
    coach_since: Optional[datetime.datetime] = None
    bank_name: Optional[str] = None
    iban_no: Optional[str] = None
    acc_holder_name: Optional[str] = None
    swift_code: Optional[str] = None

class PaginationOptions(BaseModel):
    limit: Optional[int] = None
    offset: Optional[int] = None

class UserBase(BaseModel):
    id: int
    role_id: int
    org_id: int
    class Config:
        from_attributes=True
