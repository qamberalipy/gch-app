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