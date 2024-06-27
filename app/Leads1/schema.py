
import pydantic
import datetime
from datetime import date
from typing import Optional

class LeadBase(pydantic.BaseModel):
    first_name: str
    last_name:str
    staff_id:int
    mobile:str
    status:str
    source_id:int
    lead_since:date
   
class LeadCreate(LeadBase):
    phone:str
    email:str
    notes:str
    created_by:int
    updated_by:int  

    class Config:
            from_attributes = True

class LeadRead(LeadBase):
    pass
    