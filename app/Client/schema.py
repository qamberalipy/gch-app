import pydantic
import datetime 
import datetime 
from typing import Dict, Optional, List, Any
from app.Client.models import ClientStatus

class ClientBase(pydantic.BaseModel):
    profile_img: Optional[str] = None
    own_member_id: str  
    first_name: str
    last_name: str
    gender: str
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
    height:Optional[float]=0.0 
    weight: Optional[float]=0.0 
    bmi: Optional[float]=0.0     
    circumference_waist_navel: Optional[float]=0.0
    fat_percentage: Optional[float]=0.0
    muscle_percentage: Optional[float]=0.0
    client_since: Optional[datetime.date] = None
    created_at: Optional[datetime.datetime] = None
    created_by: Optional[int] = None


class ClientCreate(ClientBase):
    org_id: int
    coach_id: Optional[List[int]] = []
    membership_plan_id: int
    status: ClientStatus="active"  # Corrected type annotation
    send_invitation: bool
    prolongation_period:Optional[int] = None
    auto_renew_days:Optional[int] = None
    inv_days_cycle:Optional[int] = None
    class Config:
        from_attributes = True
        

class ClientCreateApp(pydantic.BaseModel):
    first_name: str
    last_name: str
    gender: str
    dob: datetime.date
    email: str
    height:Optional[float]=0.0 
    weight:Optional[float]=0.0 
    bmi:Optional[float]=0.0     
    circumference_waist_navel:Optional[float]=0.0
    fat_percentage:Optional[float]=0.0
    muscle_percentage:Optional[float]=0.0
    client_since: Optional[datetime.date] = None
    notes: Optional[str] = None
    is_business: Optional[bool] = False
    country_id: Optional[int] = None
    zipcode: Optional[str] = None
    client_since: Optional[datetime.date] = None
    org_id: Optional[int] = 0
    coach_id: Optional[int] = 0
    status: Optional[ClientStatus] = None
    membership_plan_id: Optional[int] = 0
    is_deleted:Optional[bool]=False


class RegisterClientApp(pydantic.BaseModel):
    own_member_id:str
    first_name: str
    last_name: str
    gender: str
    dob: datetime.date
    email: str
    height:Optional[float]=0.0 
    weight:Optional[float]=0.0 
    bmi:Optional[float]=0.0     
    circumference_waist_navel:Optional[float]=0.0
    fat_percentage:Optional[float]=0.0
    muscle_percentage:Optional[float]=0.0
    client_since: Optional[datetime.date] = None
    notes: Optional[str] = None
    is_business: Optional[bool] = False
    country_id: Optional[int] = None
    zipcode: Optional[str] = None
    client_since: Optional[datetime.date] = None 
    is_deleted:Optional[bool]=False
    
        
class RegisterClient(ClientBase):
    pass

class ClientRead(ClientBase):
    id: int
    coach_id: Optional[List[int]]=[]
    
    class Config:
        from_attributes=True

        
class ClientLoginResponse(pydantic.BaseModel):
    is_registered: bool
    client: Optional[ClientRead] = None
    access_token: Optional[Dict[str, str]] = None
    
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
    height:Optional[float]=0.0 
    weight:Optional[float]=0.0 
    bmi:Optional[float]=0.0     
    circumference_waist_navel:Optional[float]=0.0
    fat_percentage:Optional[float]=0.0
    muscle_percentage:Optional[float]=0.0
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
    coaches: Optional[List[Dict]] = []
    org_id: Optional[int] = None
    membership_plan_id: Optional[int] = None

    class Config:
        from_attributes = True
        
class ClientOrganization(pydantic.BaseModel):
    client_id: int
    org_id: int
    client_status:ClientStatus

class CreateClientOrganization(ClientOrganization):
    pass
    
class ClientMembership(pydantic.BaseModel):
    client_id: int
    membership_plan_id: int
    prolongation_period:Optional[int] = None
    auto_renew_days:Optional[int] = None
    inv_days_cycle:Optional[int] = None

class CreateClientMembership(ClientMembership):
    pass

class ClientCoach(pydantic.BaseModel):
    client_id: int
    coach_id: List[int]

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
    total_members: int
    
class ClientList(pydantic.BaseModel):
    id: int
    name:Optional[str]=None
    
# class ClientLoginResponse(pydantic.BaseModel):
#     is_registered: bool

class ClientFilterRead(pydantic.BaseModel):
    id: int
    own_member_id: str
    first_name: str
    last_name: str
    org_id:int
    client_status:ClientStatus
    membership_plan_id:int
    phone: Optional[str]
    mobile_number: Optional[str]
    check_in: Optional[datetime.datetime]
    last_online: Optional[datetime.datetime]
    client_since: datetime.date
    business_name: Optional[str]
    coaches: Optional[List[Dict]] = []

    class Config:
        from_attributes=True

class ClientFilterParams(pydantic.BaseModel):
    
    search_key: Optional[str] = None
    member_name: Optional[str] = None
    sort_key:Optional[str]=None
    sort_order: Optional[str] = None
    coach_assigned: Optional[int] = None
    membership_plan: Optional[int] = None
    status:Optional[ClientStatus]=None
    limit:Optional[int] = 10
    offset:Optional[int] = 0
    
class ClientDelete(pydantic.BaseModel):
    id : int
    
class ClientUpdate(pydantic.BaseModel):
    id : int
    profile_img: Optional[str] = None
    own_member_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[datetime.date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile_number: Optional[str] = None
    notes: Optional[str] = None
    source_id: Optional[int] = None
    language: Optional[str] = None
    is_business: Optional[bool] = None
    business_id: Optional[int] = None
    country_id: Optional[int] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    client_since: Optional[datetime.date] = None
    updated_at: Optional[datetime.datetime] = None
    updated_by: Optional[int] = None
    height:Optional[float]=0.0 
    weight:Optional[float]=0.0 
    bmi:Optional[float]=0.0     
    circumference_waist_navel:Optional[float]=0.0
    fat_percentage:Optional[float]=0.0
    muscle_percentage:Optional[float]=0.0
    coach_id: Optional[List[int]] = []
    membership_id: Optional[int] = None
    org_id: Optional[int] = None
    status: Optional[ClientStatus] = None


    class Config:
        from_attributes = True
