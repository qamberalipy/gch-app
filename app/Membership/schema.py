import pydantic
import datetime
from datetime import date
from typing import Optional

class MembershipPlanBase(pydantic.BaseModel):
    name: str
    price: str
    org_id: int

class MembershipPlanCreate(MembershipPlanBase):
    pass

class MembershipPlanRead(MembershipPlanBase):
    id: int
    is_deleted: bool

    class Config:
        from_attributes = True
        
class CreditBase(pydantic.BaseModel):
    name: str
    org_id: int
    min_limit: int

class CreditCreate(CreditBase):
    created_by: Optional[int] = None

class CreditUpdate(CreditBase):
    updated_by: Optional[int] = None

class CreditRead(CreditBase):
    id: int
    is_deleted: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True