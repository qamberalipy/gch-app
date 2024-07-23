import pydantic
import datetime
from typing import Optional

class CoachBase(pydantic.BaseModel):
    wallet_address: Optional[str]
    org_id : Optional[str]
    own_coach_id: Optional[str]
    profile_img: Optional[str]
    first_name: str
    last_name: Optional[str]
    dob: datetime.date
    gender: Optional[str]
    email: str
    password: Optional[str]
    phone: Optional[str]
    mobile_number: Optional[str]
    notes: Optional[str]
    source_id: Optional[int]
    country_id: Optional[int]
    city: Optional[str]
    zipcode: Optional[str]
    address_1: Optional[str]
    address_2: Optional[str]
    coach_since: Optional[datetime.date]
    bank_name: Optional[str]
    iban_no: Optional[str]
    acc_holder_name: Optional[str]
    swift_code: Optional[str]
   
   
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
