
import pydantic
from datetime import date
from typing import Optional

class LeadBase(pydantic.BaseModel):
    first_name: str
    last_name:str
    staff_id:Optional[int]=None
    mobile:str
    status:str
    source_id:Optional[int]=None
    lead_since:date
    
   
class LeadCreate(LeadBase):
    phone:Optional[str]=None
    email:str
    notes:Optional[str]=None
    created_by:Optional[int]=None
    updated_by:Optional[int]=None  
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

    
    