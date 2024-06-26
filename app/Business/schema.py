import pydantic
import datetime
from datetime import date
from typing import Optional

class BusinessBase(pydantic.BaseModel):
    name: str
    address: str
    email: str
    owner_id: int
    org_id: int

class BusinessCreate(BusinessBase):
    pass

class BusinessRead(BusinessBase):
    id: int
    date_created: date
    is_deleted: bool

    class Config:
        from_attributes = True  