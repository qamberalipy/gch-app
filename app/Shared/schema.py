import datetime
from datetime import date
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field


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
    username: str
    password: Optional[str] = None
    profile_type_id: Optional[int] = None
    plan_type_id: Optional[int] = None
    source_id: Optional[int] = None
    auth_provider: Optional[str] = "local"  # 'local' or 'google'
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
    username: Optional[str]
    email: Optional[str]
    profile_type_id: Optional[int] = None
    plan_type_id: Optional[int] = None
    source_id: Optional[int] = None
    auth_provider: Optional[str] = None

    class Config:
        orm_mode = True


class AuthLoginResp(BaseModel):
    message: str
    access_token: str
    user: UserOut
