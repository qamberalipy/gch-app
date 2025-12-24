# app/user/schema.py
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from enum import Enum

# --- Enums (Must match Models) ---
class UserRoleEnum(str, Enum):
    admin = "admin"
    manager = "manager"
    team_member = "team_member"
    digital_creator = "digital_creator"

class GenderEnum(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"

# --- CRUD Requests ---

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, description="Min 6 chars")
    role: Optional[UserRoleEnum] = UserRoleEnum.team_member
    
    # Optional Profile Info
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    gender: Optional[GenderEnum] = None
    country_id: Optional[int] = None
    city: Optional[str] = None
    address_1: Optional[str] = None
    bio: Optional[str] = None

class UserUpdate(BaseModel):
    """All fields optional for PATCH/PUT updates"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    mobile_number: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[GenderEnum] = None
    dob: Optional[date] = None
    country_id: Optional[int] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None

# --- Responses ---

class UserOut(BaseModel):
    id: int
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    account_status: Optional[str] = None
    
    # Contact
    phone: Optional[str] = None
    profile_picture_url: Optional[str] = None
    
    # Flags
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True