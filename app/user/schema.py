import pydantic
import datetime
from datetime import date
from typing import Optional

class UserBase(pydantic.BaseModel):
    username: str
    email: str
    class Config:
        from_attributes=True

class UserCreate(UserBase): 
    password: str
    org_name: str
    class Config:
        from_attributes=True
       
class UserRegister(UserBase):
    password: str
    date_created: datetime.datetime
    org_id: int
    class Config:
        from_attributes=True

class User(UserBase):
    id: int
    date_created: datetime.datetime
    class Config:
        from_attributes=True

class GenerateUserToken(pydantic.BaseModel):
    email: str
    password: str
    class Config:
       from_attributes=True

class GenerateOtp(pydantic.BaseModel):
    email: str
    
class VerifyOtp(pydantic.BaseModel):
    email: str
    otp: int

class ClientBase(pydantic.BaseModel):
    profile_url:str
    own_member_id: str
    first_name: str
    last_name: str
    sex: str
    date_of_birth: date
    email_address: str
    landline_number: Optional[str] = None
    mobile_number: Optional[str] = None
    client_since: date
    subscription_reason: Optional[str] = None
    source: Optional[str] = None
    language: Optional[str] = None
    is_business: bool = False
    country: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    address: Optional[str] = None
    bank_account_number: Optional[str] = None
    bic_swift_code: Optional[str] = None
    bank_account_holder_name: Optional[str] = None
    bank_name: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientRead(ClientBase):
    id: int
    
    class Config:
        from_attributes=True

class ClientLogin(pydantic.BaseModel):
    email_address: str
    wallet_address: str

class BankAccountCreate(pydantic.BaseModel):
    bank_account_number: str
    bic_swift_code: str
    bank_account_holder_name: str
    bank_name: str
    
class OrganizationCreate(pydantic.BaseModel):
    org_name: str