import pydantic
import datetime
from typing import Dict, List, Optional
from app.Membership.models import MembershipStatus

class MembershipPlanBase(pydantic.BaseModel):
    name: Optional[str] = None
    org_id: Optional[int] = None
    group_id: Optional[int] = None
    status: Optional[MembershipStatus] = "active"
    description: Optional[str] = None
    access_time: Optional[Dict] = None
    net_price: Optional[float] = None
    income_category_id: Optional[int] = None
    discount: Optional[float] = None
    total_price: Optional[float] = None
    payment_method: Optional[str] = None
    reg_fee: Optional[float] = None
    billing_cycle: Optional[str] = None
    auto_renewal: Optional[bool] = None
    renewal_details: Optional[Dict] = None

class FacilityMembershipPlan(pydantic.BaseModel):
    id: int
    total_credits: int
    validity: Dict

class MembershipPlanCreate(MembershipPlanBase):
    facilities: Optional[List[FacilityMembershipPlan]]=[]
    created_by: int

class MembershipPlanUpdate(MembershipPlanBase):
    id:int
    facilities: Optional[List[FacilityMembershipPlan]]=[]
    updated_by: Optional[int]=None 

class MembershipPlanDelete(pydantic.BaseModel):
    id:int

class MembershipPlanRead(MembershipPlanBase):
    id: int
    created_by: Optional[int]=None
    created_at: Optional[datetime.datetime]=None
    updated_at: Optional[datetime.datetime]=None

    class Config:
        from_attributes = True
        
class FacilityBase(pydantic.BaseModel):
    name: Optional[str] = None
    org_id: Optional[int] = None
    min_limit: Optional[int] = None
    status: Optional[MembershipStatus] = "active"

class FacilityDelete(pydantic.BaseModel):
    id: int  # Correctly annotated with the type int

    class Config:
        from_attributes = True
    
class FacilityCreate(FacilityBase):
    created_by: Optional[int] = None

class FacilityUpdate(FacilityBase):
    id:int
    updated_by: Optional[int] = None

class FacilityRead(FacilityBase):
    id: int
    is_deleted: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
        
class FacilityFilterParams(pydantic.BaseModel):
    search_key: Optional[str] = None
    sort_key:Optional[str]=None
    sort_order: Optional[str] = 'desc'
    status: Optional[MembershipStatus] = None
    limit:Optional[int] = None
    offset:Optional[int] = None


class data_list(pydantic.BaseModel):
    id:Optional[int]=None    
    name:Optional[str]=None
    status : Optional[MembershipStatus] = None
    min_limit : Optional[int] = None  


class data_list_income_category(pydantic.BaseModel):
    id:Optional[int]=None    
    name:Optional[str]=None    
    sale_tax_id:Optional[int]=None

class data_list_saletax(pydantic.BaseModel):
    id:Optional[int]=None    
    name:Optional[str]=None    
    percentage:Optional[float]=None
    
class IncomeCategoryBase(pydantic.BaseModel):
    name: Optional[str] = None
    position: Optional[int] = None
    status:Optional[MembershipStatus]="active"
    sale_tax_id: Optional[int] = None
    org_id: Optional[int] = None

class IncomeCategoryCreate(IncomeCategoryBase):
    created_by: Optional[int] = None

class IncomeCategoryUpdate(IncomeCategoryBase):
    id: Optional[int] = None
    updated_by: Optional[int] = None

class IncomeCategoryDelete(pydantic.BaseModel):
    id: int 
    class Config:
        from_attributes = True

class IncomeCategoryRead(IncomeCategoryBase):
    id: Optional[int] = None
    is_deleted: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

class IncomeCategoryFilterParams(pydantic.BaseModel):
    search_key: Optional[str] = None
    sort_order: Optional[str] = 'desc'
    sort_key : Optional[str] = None
    status: Optional[MembershipStatus] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
        
class SaleTaxBase(pydantic.BaseModel):
    name: Optional[str] = None
    percentage: Optional[float] = None
    status: Optional[MembershipStatus] = "active"
    org_id: Optional[int] = None

class SaleTaxCreate(SaleTaxBase):
    created_by: Optional[int] = None

class SaleTaxUpdate(SaleTaxBase):
    id: Optional[int] = None
    updated_by: Optional[int] = None

class SaleTaxRead(SaleTaxBase):
    id: Optional[int] = None
    is_deleted: bool
    created_at: Optional[datetime.datetime]=None
    updated_at: Optional[datetime.datetime]=None
    created_by: Optional[int] = 0
    updated_by: Optional[int] = 0

    class Config:
        from_attributes = True

class SaleTaxDelete(pydantic.BaseModel):
    id: int 

    class Config:
        from_attributes = True


class GroupCreate(pydantic.BaseModel):
    org_id: int
    name: str
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

class GroupRead(pydantic.BaseModel):
    id: int
    name: str
    org_id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class GroupUpdate(pydantic.BaseModel):
    id: int
    name: Optional[str] = None


class SaleTaxFilterParams(pydantic.BaseModel):
    search_key:Optional[str] = None
    sort_order:Optional[str]="asc"
    sort_key:Optional[str]=None
    status:Optional[MembershipStatus]=None
    limit:Optional[int]= None
    offset:Optional[int] = None

class MembershipFilterParams(pydantic.BaseModel):
    group_id: Optional[int] = None
    income_category_id: Optional[int] = None
    discount_percentage: Optional[float] = None
    total_amount: Optional[float] = None
    status: Optional[MembershipStatus] = None
    search_key: Optional[str] = None
    sort_order: Optional[str] = "asc"
    limit: Optional[int] = 10
    offset: Optional[int] = 0

class StandardParams(pydantic.BaseModel):
    org_id: int
    search_key: Optional[str] = None
    sort_order: Optional[str] = "desc"
    limit: Optional[int] = 10
    offset: Optional[int] = 0

class MembershipPlanResponse(pydantic.BaseModel):
    id:Optional[int] = None
    name:  Optional[str] = None
    org_id: Optional[int] = None
    group_id: Optional[int] = None
    status:  Optional[MembershipStatus] = None
    description:  Optional[str] = None
    access_time: Optional[Dict] =[] 
    net_price: Optional[float] = None
    income_category_id: Optional[int] = None
    discount: Optional[float] = None
    total_price: Optional[float] = None
    payment_method:  Optional[str] = None
    reg_fee: Optional[float] = None
    billing_cycle:  Optional[str] = None
    auto_renewal: Optional[bool] = None
    renewal_details: Optional[Dict] =[] 
    facilities: Optional[List[FacilityMembershipPlan]]=[]
    created_by: Optional[int] = None
    