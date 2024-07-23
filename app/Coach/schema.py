import pydantic
import datetime
from typing import Dict, Optional

class CoachBase(pydantic.BaseModel):
    wallet_address: Optional[str]=None 
    org_id : Optional[str]=None
    own_coach_id: Optional[str]=None
    profile_img: Optional[str]=None
    first_name: str
    last_name: Optional[str]=None
    dob: datetime.date
    gender: Optional[str]=None
    email: str
    password: Optional[str]=None
    phone: Optional[str]=None
    mobile_number: Optional[str]=None
    notes: Optional[str]=None
    source_id: Optional[int]=None
    country_id: Optional[int]=None
    city: Optional[str]=None
    zipcode: Optional[str]=None
    address_1: Optional[str]=None
    address_2: Optional[str]=None
    coach_since: Optional[datetime.date]=None
    bank_name: Optional[str]=None
    iban_no: Optional[str]=None
    acc_holder_name: Optional[str]=None
    swift_code: Optional[str]=None
   
   
class CoachCreate(CoachBase):
    created_by: int

class CoachUpdate(CoachBase):
    id:int
    updated_by:  Optional[int]

class CoachRead(CoachBase):
    id: int
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

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
   
