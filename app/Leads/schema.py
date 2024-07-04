
import pydantic
from datetime import date
from typing import Optional

class LeadBase(pydantic.BaseModel):
    first_name: str
    last_name:str
    staff_id:Optional[int]=None
    mobile:Optional[str]=None
    status:str
    source_id:Optional[int]=None
    lead_since:date
    
   
class LeadCreate(LeadBase):
    phone:Optional[str]=None
    email:Optional[str]=None
    notes:Optional[str]=None
    created_by:Optional[int]=None
    updated_by:Optional[int]=None  
    org_id:int

    class Config:
            from_attributes = True

class LeadRead(pydantic.BaseModel):
    org_id:int
    limit:Optional[int]=None
    offset:Optional[int]=None
    first_name:Optional[str]
    mobile:Optional[str]
    owner:Optional[str]
    status:Optional[str]
    source:Optional[str]
    search:Optional[str]

    class Config:
            from_attributes = True
class UpdateStaff(pydantic.BaseModel):
      lead_id :int
      staff_id:int

class UpdateStatus(pydantic.BaseModel):
      lead_id :int
      status:str    

class ResponseLeadRead(pydantic.BaseModel):
    id:Optional[int]
    name:Optional[str]
    email:Optional[str]
    mobile:Optional[str]
    status:Optional[str]
    source:Optional[str]
    owner:Optional[str]
    lead_since:Optional[date]
    class Config:
            from_attributes = True

    
class LeadUpdate(pydantic.BaseModel):
    first_name: Optional[str]=None
    last_name:Optional[str]=None
    staff_id:Optional[int]=None
    mobile:Optional[str]=None
    status:Optional[str]=None
    source_id:Optional[int]=None
    phone:Optional[str]=None
    email:Optional[str]=None
    notes:Optional[str]=None
    updated_by:Optional[int]=None  
    class Config:
            from_attributes = True
          