import pydantic
import datetime
from datetime import date,datetime
from typing import Optional

class ClientBase(pydantic.BaseModel):
    profile_img: Optional[str] = None
    own_member_id: str
    first_name: str
    last_name: str
    gender: str
    dob: date
    email: str
    phone: Optional[str] = None
    mobile_number: Optional[str] = None
    notes: Optional[str] = None
    source_id: Optional[int] = None
    language: Optional[str] = None
    is_business: bool = False
    business_id: Optional[int] = None
    country_id: Optional[int] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    client_since: Optional[date] = None
    created_at: Optional[datetime.datetime] = None
    created_by: Optional[int] = None

class ClientCreate(ClientBase):
    org_id: int
    coach_id: int
    membership_id: int
    status: str  # Corrected type annotation
    send_invitation: bool
    
    class Config:
        from_attributes = True


class RegisterClient(ClientBase):
    pass

class ClientRead(ClientBase):
    id: int
    
    class Config:
        from_attributes=True

class ClientOrganization(pydantic.BaseModel):
    client_id: int
    org_id: int
    client_status:str

class CreateClientOrganization(ClientOrganization):
    pass
    
class ClientMembership(pydantic.BaseModel):
    client_id: int
    membership_plan_id: int

class CreateClientMembership(ClientMembership):
    pass

class ClientCoach(pydantic.BaseModel):
    client_id: int
    coach_id: int

class CreateClientCoach(ClientCoach):
    pass
    
class ClientLogin(pydantic.BaseModel):
    email_address: str
    wallet_address: str
    
class BusinessBase(pydantic.BaseModel):
    name: str
    address: str
    email: str
    org_id: int

class BusinessRead(BusinessBase):
    id: int
    date_created: date

    class Config:
        from_attributes=True


class ClientBusinessRead(pydantic.BaseModel):
    id: int
    first_name: str
        
class ClientCount(pydantic.BaseModel):
    total_clients: int
    
class ClientLoginResponse(pydantic.BaseModel):
    is_registered: bool

class ClientFilterRead(pydantic.BaseModel):
    id: int
    wallet_address: Optional[str]
    profile_img: Optional[str]
    own_member_id: str
    first_name: str
    last_name: str
    gender: Optional[str]
    dob: date
    email: str
    phone: Optional[str]
    mobile_number: Optional[str]
    notes: Optional[str]
    source_id: Optional[int]
    language: Optional[str]
    is_business: Optional[bool]
    business_id: Optional[int]
    country_id: Optional[int]
    city: Optional[str]
    zipcode: Optional[str]
    address_1: Optional[str]
    address_2: Optional[str]
    activated_on: Optional[date]
    check_in: Optional[datetime]
    last_online: Optional[datetime]
    client_since: date
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    created_by: Optional[int]
    updated_by: Optional[int]
    is_deleted: Optional[bool]

    class Config:
        from_attributes=True

class ClientFilterParams(pydantic.BaseModel):
    org_id: int
    search_key: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[str] = None
    coach_assigned: Optional[int] = None
    membership_plan: Optional[int] = None
    