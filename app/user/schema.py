import pydantic
import datetime
from datetime import date
from typing import Optional, List, Any

class UserBase(pydantic.BaseModel):
    first_name: str
    email: str
    class Config:
        from_attributes=True

class UserCreate(UserBase): 
    password: str
    org_name: str
    class Config:
        from_attributes=True
       
class UserRegister(UserBase):
    password: str
    created_at: datetime.datetime
    org_id: int
    class Config:
        from_attributes=True

class User(UserBase):
    id: int
    created_at: datetime.datetime
    class Config:
        from_attributes=True

class GenerateUserToken(pydantic.BaseModel):
    email: str
    password: str
    class Config:
       from_attributes=True

class GenerateOtp(pydantic.BaseModel):
    email: str
    
class VerifyOtp(pydantic.BaseModel):
    email: str
    otp: int
        
class BankAccountCreate(pydantic.BaseModel):
    bank_account_number: str
    bic_swift_code: str
    bank_account_holder_name: str
    bank_name: str
    
class OrganizationCreate(pydantic.BaseModel):
    org_name: str

class getStaff(pydantic.BaseModel):
    
    org_id:int
    id:Optional[int]
    first_name:Optional[str]
    class Config:
       from_attributes=True

class getPrivileges(pydantic.BaseModel):
    id:int
    name:str
    
    
    
class CountryRead(pydantic.BaseModel):
    id: int
    country: str
    country_code: int
    is_deleted: bool

    class Config:
        from_attributes = True

class SourceRead(pydantic.BaseModel):
    id: int
    source: str

    class Config:
        from_attributes = True

class StaffCount(pydantic.BaseModel):
    total_staffs: int

class StaffBase(pydantic.BaseModel):
    own_staff_id: Optional[str] = None
    profile_img: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[datetime.datetime]=None
    email: str
    phone: Optional[str] = None
    mobile_number: Optional[str] = None
    notes: Optional[str] = None
    source_id: Optional[int] = None
    org_id: Optional[int] = None
    role_id: Optional[int] = None
    country_id: Optional[int] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    status: Optional[str] = None
    send_invitation: Optional[bool]=False
    
    class Config:
        from_attributes = True

class CreateStaff(StaffBase):
    created_at: Optional[datetime.datetime] = datetime.datetime.now()
    created_by: Optional[int] = None

class ReadStaff(StaffBase):
    id:int
    activated_on: Optional[datetime.date] = None
    last_online: Optional[datetime.datetime] = None
    last_checkin: Optional[datetime.datetime] = None
    
class GetStaffResponse(StaffBase):
    id:int
    role_name:Optional[str] = None
    activated_on: Optional[datetime.date] = None
    last_online: Optional[datetime.datetime] = None
    last_checkin: Optional[datetime.datetime] = None
    
class StaffDetail(pydantic.BaseModel):
    id: int
    own_staff_id: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    email: str
    mobile: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    profile_img: Optional[str] = None
    activated_on: Optional[datetime.date] = None
    last_online: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True
        
class DeleteStaff(pydantic.BaseModel):
    id:int
            
class UpdateStaff(pydantic.BaseModel):
    id:int
    profile_img: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[datetime.datetime] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile_number: Optional[str] = None
    notes: Optional[str] = None
    source_id: Optional[int] = None
    org_id: Optional[int] = None
    role_id: Optional[int] = None
    country_id: Optional[int] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    status: Optional[str] = None
    activated_on: Optional[datetime.date] = None
    last_online: Optional[datetime.datetime] = None
    updated_by: Optional[int] = None
    updated_at: Optional[datetime.datetime] = None
    
    class Config:
        from_attributes = True
        
class StaffFilterParams(pydantic.BaseModel):
    search_key: Optional[str] = None
    staff_name: Optional[str] = None
    role_name: Optional[str] = None
    sort_order: Optional[str] = "asc"
    limit: Optional[int] = 10
    offset: Optional[int] = 0

class StaffFilterRead(pydantic.BaseModel):
    id: Optional[int] = None
    own_staff_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    profile_img: Optional[str] = None

    class Config:
        from_attributes = True

class RoleBase(pydantic.BaseModel):
    name: str
    org_id: Optional[int] = None
    status: Optional[bool] = None
    is_deleted: Optional[bool] = False

    class Config:
        from_attributes = True


class RoleCreate(RoleBase):
    resource_id: List[int]
    access_type: List[str]
    created_at: Optional[datetime.datetime] = datetime.datetime.now()
    created_by: Optional[int] = None

class RoleDelete(pydantic.BaseModel):
    id: int

    class Config:
        from_attributes = True

class RoleRead(pydantic.BaseModel):
    resource_name: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    org_id: Optional[int] = None
    status: Optional[bool] = None
    permission_id: Optional[int] = None
    resource_id: Optional[int] = None
    access_type: Optional[str] = None
    is_parent: Optional[bool] = None
    is_root: Optional[bool] = None
    parent: Optional[str] = None
    code: Optional[str] = None
    link: Optional[str] = None
    icon: Optional[str] = None
    is_deleted: Optional[bool] = False
    # resources: Optional[List['RoleRead']] = None
    children: Optional[List['RoleRead']] = []

    class Config:
        from_attributes = True

RoleRead.update_forward_refs()
# class RoleSingleRead(pydantic.BaseModel):
#     name: str
#     access_type: str

#     class Config:
#         from_attributes = True

class RoleUpdate(pydantic.BaseModel):
    id: int
    name: Optional[str] = None
    org_id: int
    status: Optional[bool] = None
    resource_id: Optional[List[int]] = None
    access_type: Optional[List[str]] = None
    created_at: Optional[datetime.datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    updated_at: Optional[datetime.datetime] = None
    is_deleted: Optional[bool] = False

    class Config:
        from_attributes = True
        extra = "forbid"

class ResourceRead(pydantic.BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    parent: Optional[str] = None
    is_parent: Optional[bool] = None
    is_root: Optional[bool] = None
    link: Optional[str] = None
    icon: Optional[str] = None
    children: Optional[List['ResourceRead']] = []

    class Config:
        from_attributes = True

ResourceRead.update_forward_refs()