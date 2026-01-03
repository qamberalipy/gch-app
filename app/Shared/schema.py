from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum

# --- Enums (Matching models.py) ---
class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    team_member = "team_member"
    digital_creator = "digital_creator"

class Gender(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"

# ---- Requests ----

class LoginReq(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordReq(BaseModel):
    email: EmailStr

class ResetPasswordReq(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(..., min_length=6)

class RefreshReq(BaseModel):
    refresh_token: str

class CreateUserReq(BaseModel):
  
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.digital_creator
    gender: Optional[Gender] = None
    
    # Optional fields
    phone: Optional[str] = None
    country_id: Optional[int] = None
    city: Optional[str] = None
    timezone: Optional[str] = "UTC" # Default to UTC if not provided
    dob: Optional[str] = None # Expecting YYYY-MM-DD string

# ---- Responses ----

class UserOut(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole
    is_onboarded: bool
    timezone: Optional[str] = None
    profile_picture_url: Optional[str] = None
    # Additional info
    phone: Optional[str] = None
    gender: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class AuthLoginResp(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    user: UserOut

class MessageResp(BaseModel):
    message: str

class CountryOut(BaseModel):
    id: int
    country: str
    country_code: Optional[str] = None

    class Config:
        orm_mode = True