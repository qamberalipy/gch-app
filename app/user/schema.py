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
    created_at: datetime.datetime
    org_id: int
    class Config:
        from_attributes=True

class User(UserBase):
    id: int
    created_at: datetime.datetime
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
        
class BankAccountCreate(pydantic.BaseModel):
    bank_account_number: str
    bic_swift_code: str
    bank_account_holder_name: str
    bank_name: str
    
class OrganizationCreate(pydantic.BaseModel):
    org_name: str

class getStaff(pydantic.BaseModel):
    
    org_id:int
    id:Optional[int]
    username:Optional[str]
    class Config:
       from_attributes=True

    
    
    
class CountryRead(pydantic.BaseModel):
    id: int
    country: str
    country_code: int
    is_deleted: bool

    class Config:
        from_attributes = True

class SourceRead(pydantic.BaseModel):
    id: int
    source: str

    class Config:
        from_attributes = True