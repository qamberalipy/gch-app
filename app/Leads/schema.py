
import pydantic
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
    org_id:int

    class Config:
            from_attributes = True

class LeadRead(pydantic.BaseModel):
    org_id:int
    first_name:Optional[str]
    mobile:Optional[str]
    owner:Optional[str]
    status:Optional[str]
    source:Optional[str]
    search:Optional[str]

    class Config:
            from_attributes = True

    
class ResponseLeadRead(pydantic.BaseModel):
    first_name:Optional[str]
    mobile:Optional[str]
    status:Optional[str]
    source:Optional[str]
    owner:Optional[str]
    lead_since:Optional[date]
    class Config:
            from_attributes = True

    
    