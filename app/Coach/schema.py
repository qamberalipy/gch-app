import pydantic
import datetime
from typing import Dict, List, Optional
from app.Coach.models import CoachStatus
from sqlalchemy import JSON


class CoachList(pydantic.BaseModel):
    id:Optional[int]
    name:Optional[str]

class CoachBase(pydantic.BaseModel):
    wallet_address: Optional[str] = None 
    org_id: Optional[int] = None
    coach_status: Optional[CoachStatus]="active"
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

class CoachCreate(CoachBase):
    created_by: int
    member_ids: Optional[List[int]] = None

class CoachUpdate(CoachBase):
    id: int
    updated_by: Optional[int] = None
    member_ids: Optional[List[int]] = []

class CoachRead(CoachBase):
    id:int
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class CoachDelete(pydantic.BaseModel):
    id: int
    class Config:
        from_attributes = True

class CoachAppBase(pydantic.BaseModel):
    org_id: Optional[int] = None
    first_name: str
    last_name: Optional[str] = None
    dob: datetime.date
    gender: Optional[str] = None
    email: str
    phone: Optional[str] = None
    mobile_number: Optional[str] = None
    notes: Optional[str] = None
    country_id: Optional[int] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    coach_since: Optional[datetime.date] = None
    bank_name: Optional[str] = None
    iban_no: Optional[str] = None
    is_deleted: Optional[bool] = False
    acc_holder_name: Optional[str] = None
    swift_code: Optional[str] = None
    updated_by:Optional[int]=0
    member_ids: Optional[List[int]] = None
    coach_status: Optional[CoachStatus] = None
    check_in: Optional[datetime.datetime] = None
    last_online: Optional[datetime.datetime] = None
    coach_since: Optional[datetime.datetime] = None

class CoachLogin(pydantic.BaseModel):
    email_address: str
    wallet_address: str

class CoachLoginResponse(pydantic.BaseModel):
    is_registered: bool
    coach: Optional[CoachRead] = []
    access_token: Optional[Dict[str, str]] = None
    
class CoachCount(pydantic.BaseModel):
    total_coaches: int
    
class CoachFilterParams(pydantic.BaseModel):
    search_key: Optional[str] = None
    sort_order: Optional[str] = None
    sort_key: Optional[str] =None
    status: Optional[CoachStatus] = None
    limit:Optional[int] = None
    offset:Optional[int] = None
    
class CoachReadSchema(pydantic.BaseModel):
    id: int
    own_coach_id: Optional[str] = None
    profile_img: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[datetime.date] = None
    gender: Optional[str] = None
    email: Optional[str] = None
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
    coach_status: Optional[CoachStatus] = None
    org_id: Optional[int] = None
    bank_name: Optional[str] = None
    iban_no: Optional[str] = None
    acc_holder_name: Optional[str] = None
    swift_code: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    members: Optional[List[int]] = []
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed=True

   
class CoachResponse(pydantic.BaseModel):
    id: int
    wallet_address: Optional[str]
    own_coach_id: Optional[str]
    profile_img: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    dob: Optional[datetime.date]
    gender: Optional[str]
    email: Optional[str]
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
    check_in: Optional[datetime.datetime]
    last_online: Optional[datetime.datetime]
    coach_since: Optional[datetime.datetime]
    bank_detail_id: Optional[int]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    created_by: Optional[int]
    updated_by: Optional[int]
    is_deleted: bool
    coach_status: CoachStatus
    org_id: int
    bank_name: Optional[str]
    iban_no: Optional[str]
    acc_holder_name: Optional[str]
    swift_code: Optional[str]
    members: List[int]

    class Config:
        from_attributes = True