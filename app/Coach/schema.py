import pydantic
import datetime
from typing import Dict, List, Optional

class CoachBase(pydantic.BaseModel):
    wallet_address: Optional[str] = None 
    org_id : Optional[int] = None
    own_coach_id: Optional[str] = None
    profile_img: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[datetime.date]=None
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
    coach_since: Optional[datetime.date] = None
    bank_name: Optional[str] = None
    iban_no: Optional[str] = None
    acc_holder_name: Optional[str] = None
    swift_code: Optional[str] = None
   
   
class CoachCreate(CoachBase):
    created_by: int
    member_ids: Optional[List[int]] = None  # Add this line to include member IDs


class CoachUpdate(CoachBase):
    id:int
    updated_by:  Optional[int]=None
    member_ids: Optional[List[int]] = None  # Add member IDs here

class CoachRead(CoachBase):
    id: int
    created_at: Optional[datetime.datetime]=None
    updated_at: Optional[datetime.datetime]=None

    class Config:
        from_attributes = True

class CoachDelete(pydantic.BaseModel):
    id:int
    class Config:
            from_attributes = True

class CoachAppBase(pydantic.BaseModel):
   
    org_id : Optional[str]=None
    first_name: str
    last_name: Optional[str]=None
    dob: datetime.date
    gender: Optional[str]=None
    email: str
    phone: Optional[str]=None
    mobile_number: Optional[str]=None
    notes: Optional[str]=None
    country_id: Optional[int]=None
    city: Optional[str]=None
    zipcode: Optional[str]=None
    address_1: Optional[str]=None
    address_2: Optional[str]=None
    coach_since: Optional[datetime.date]=None
    
class CoachLogin(pydantic.BaseModel):
    email_address: str
    wallet_address: str
    
class CoachLoginResponse(pydantic.BaseModel):
    is_registered: bool
    coach: Optional[CoachRead] = None
    access_token: Optional[Dict[str, str]] = None
   
