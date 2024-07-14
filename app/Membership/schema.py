import pydantic
import datetime
from typing import Dict, Optional


class MembershipPlanBase(pydantic.BaseModel):
    name: str
    org_id: int
    group_id: Optional[int]
    status: Optional[str]
    description: Optional[str]
    access_time: Optional[Dict]
    net_price: Optional[float]
    income_category_id: Optional[int]
    discount: Optional[float]
    total_price: Optional[float]
    payment_method: Optional[str]
    reg_fee: Optional[float]
    billing_cycle: Optional[str]
    auto_renewal: Optional[bool]
    renewal_details: Optional[Dict]
    credit_id: Optional[int]

class MembershipPlanCreate(MembershipPlanBase):
    created_by: int

class MembershipPlanUpdate(MembershipPlanBase):
    id:int
    updated_by: Optional[int]

class MembershipPlanDelete(MembershipPlanBase):
    id:int

class MembershipPlanRead(MembershipPlanBase):
    id: int
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
        
class CreditBase(pydantic.BaseModel):
    name: Optional[str] = None
    org_id: Optional[int] = None
    min_limit: Optional[int] = None
    status: Optional[bool] = True

class CreditDelete(pydantic.BaseModel):
    id: int  # Correctly annotated with the type int

    class Config:
        from_attributes = True
    
class CreditCreate(CreditBase):
    created_by: Optional[int] = None

class CreditUpdate(CreditBase):
    id:int
    updated_by: Optional[int] = None

class CreditRead(CreditBase):
    id: int
    is_deleted: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
        
class IncomeCategoryBase(pydantic.BaseModel):
    name: Optional[str] = None
    position: Optional[int] = None
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
        
class SaleTaxBase(pydantic.BaseModel):
    name: Optional[str] = None
    percentage: Optional[float] = None
    org_id: Optional[int] = None

class SaleTaxCreate(SaleTaxBase):
    created_by: Optional[int] = None

class SaleTaxUpdate(SaleTaxBase):
    id: Optional[int] = None
    updated_by: Optional[int] = None

class SaleTaxRead(SaleTaxBase):
    id: Optional[int] = None
    is_deleted: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

class SaleTaxDelete(pydantic.BaseModel):
    id: int 

    class Config:
        from_attributes = True
    