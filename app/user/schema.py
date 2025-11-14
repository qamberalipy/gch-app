# app/user/schema.py
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# ---- Requests ----
class CheckEmailReq(BaseModel):
    email: EmailStr


class SendOtpReq(BaseModel):
    email: EmailStr


class VerifyOtpReq(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=10)


class CheckUsernameReq(BaseModel):
    username: str = Field(..., min_length=3)


class RegisterReq(BaseModel):
    email: EmailStr
    username: Optional[str]
    password: Optional[str] = Field(None, min_length=6)
    profile_type_id: Optional[int] = None
    plan_type_id: Optional[int] = None
    source_id: Optional[int] = None
    auth_provider: Optional[str] = "local"
    google_id: Optional[str] = None


class GoogleLoginReq(BaseModel):
    id_token: str


class LoginReq(BaseModel):
    email: EmailStr
    password: str


class RefreshReq(BaseModel):
    refresh_token: str


class ForgotPasswordReq(BaseModel):
    email: EmailStr


class ResetPasswordReq(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(..., min_length=6)


# ---- Responses ----
class ExistsResp(BaseModel):
    exists: bool


class MessageResp(BaseModel):
    message: str


class VerifyResp(BaseModel):
    verified: bool
    temp_token: Optional[str] = None


class UsernameAvailResp(BaseModel):
    available: bool


class UserOut(BaseModel):
    id: int
    username: Optional[str] = None
    email: Optional[str] = None
    profile_type_id: Optional[int] = None
    plan_type_id: Optional[int] = None
    source_id: Optional[int] = None
    auth_provider: Optional[str] = None
    is_verified: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class AuthLoginResp(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    user: UserOut
