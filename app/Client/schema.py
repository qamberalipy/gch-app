import pydantic
import datetime 
import datetime 
from typing import Optional

class ClientBase(pydantic.BaseModel):
    profile_img: Optional[str] = None
    own_member_id: str
    first_name: str
    last_name: str
    gender: str
    dob: datetime.date
    dob: datetime.date
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
    client_since: Optional[datetime.date] = None
    client_since: Optional[datetime.date] = None
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
        
class ClientByID(pydantic.BaseModel):
    id: int
    wallet_address: Optional[str] = None
    profile_img: Optional[str] = None
    own_member_id: str
    first_name: str
    last_name: str
    gender: Optional[str] = None
    dob: Optional[datetime.date] = None
    email: str
    phone: Optional[str] = None
    mobile_number: Optional[str] = None
    notes: Optional[str] = None
    source_id: Optional[int] = None
    language: Optional[str] = None
    is_business: bool
    business_id: Optional[int] = None
    country_id: Optional[int] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    activated_on: Optional[datetime.date] = None
    check_in: Optional[datetime.datetime] = None
    last_online: Optional[datetime.datetime] = None
    client_since: datetime.date
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_deleted: bool
    business_name: Optional[str] = None
    coach_id: Optional[int] = None
    org_id: Optional[int] = None
    membership_plan_id: Optional[int] = None

    class Config:
        from_attributes = True
        
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
    date_created: datetime.date
    date_created: datetime.date

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
    own_member_id: str
    first_name: str
    last_name: str
    phone: Optional[str]
    mobile_number: Optional[str]
    check_in: Optional[datetime.datetime]
    last_online: Optional[datetime.datetime]
    client_since: datetime.date
    business_name: Optional[str]
    coach_name: Optional[str]

    class Config:
        from_attributes=True

class ClientFilterParams(pydantic.BaseModel):
    org_id: int
    search_key: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[str] = None
    coach_assigned: Optional[int] = None
    membership_plan: Optional[int] = None