from typing import Annotated, Dict, List, Optional
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, DataError
import app.user.schema as _schemas
import sqlalchemy.orm as _orm
import app.user.models as _models
import app.user.service as _services
import app.Shared.schema as _h_schema
import app.core.db.session as _database
import pika
import logging
import datetime
from datetime import datetime as _dt
import fastapi.security as _security
import app.Shared.helpers as _helpers

router = APIRouter()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

login_attempts: Dict[str, int] = {}
lockout_expiry: Dict[str, datetime.datetime] = {}
MAX_ATTEMPTS = 3
LOCKOUT_TIME = datetime.timedelta(minutes=30)

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/organizations", response_model=_schemas.OrganizationRead, tags=["Organizations API"])
async def create_organization(org: _schemas.OrganizationCreate, db: _orm.Session = Depends(get_db)):
    try:
        
        if not _helpers.validate_email(org.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
  
        new_org = await _services.create_organization(org, db)
        return new_org
    
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Duplicate entry or integrity constraint violation")

    except DataError as e:
        db.rollback()
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
 

@router.get("/organizations/{id}", response_model=_schemas.OrganizationRead, tags=["Organizations API"])
async def get_organization(id: int, db: _orm.Session = Depends(get_db)):
    org = await _services.get_organization(id, db)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@router.put("/organizations", response_model=_schemas.OrganizationRead, tags=["Organizations API"])
async def update_organization(org: _schemas.OrganizationUpdate, db: _orm.Session = Depends(get_db)):
    
    if not _helpers.validate_email(org.email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    updated_org = await _services.update_organization(org.id, org, db)
    if updated_org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return updated_org

@router.delete("/organizations/{id}", response_model=_schemas.OrganizationRead, tags=["Organizations API"])
async def delete_organization(id: int, db: _orm.Session = Depends(get_db)):
    deleted_org = await _services.delete_organization(id, db)
    if deleted_org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return deleted_org

@router.get("/opening_hours/{id}", response_model=_schemas.OpeningHoursRead, tags=["Organizations API"])
async def read_opening_hours(id: int, db: _orm.Session = Depends(get_db)):
    organization = await _services.get_opening_hours(id, db)
    if organization:
        return organization
    raise HTTPException(status_code=404, detail="Organization not found")

@router.put("/opening-hours", response_model=_schemas.OpeningHoursRead, tags=["Organizations API"])
async def update_opening_hours(opening_hours_data: _schemas.OpeningHoursUpdate, db: _orm.Session = Depends(get_db)):
    updated_organization = await _services.update_opening_hours(opening_hours_data.id, opening_hours_data, db)
    if updated_organization:
        return updated_organization
    raise HTTPException(status_code=404, detail="Organization not found")

@router.get("/staff/list",response_model=List[_schemas.getStaff],tags=["Staff APIs"])
async def get_staff_list(org_id:int, db: _orm.Session= Depends(get_db)):
    
    filtered_users =  db.query(_models.User.id,func.concat(_models.User.first_name,' ',_models.User.last_name).label('name')).filter(_models.User.org_id == org_id, _models.User.is_deleted == False).all()
    return filtered_users


@router.get("/privileges",response_model=List[_schemas.getPrivileges],tags=["Staff APIs"])
async def get_privileges(org_id:int, db: _orm.Session= Depends(get_db)):
    
    
    organization_roles=  db.query(_models.Role).filter(_models.Role.org_id == org_id and _models.Role.is_deleted==False).all()
    return organization_roles


@router.post("/staff", tags=["Staff APIs"])
async def register_staff(staff: _schemas.CreateStaff, db: _orm.Session = Depends(get_db)):
    try:
        
        db_staff = await _services.get_user_by_email(staff.email, db)
        if db_staff:
            raise HTTPException(status_code=400, detail="Email already registered")

        new_staff = await _services.create_staff(staff, db)
        return new_staff

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Duplicate entry or integrity constraint violation")

    except DataError as e:
        db.rollback()
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.get("/staff/{id}", response_model=_schemas.GetStaffResponse, tags=["Staff APIs"])
async def get_staff_by_id(id: int, db: _orm.Session = Depends(get_db)):
    try:
        print("Fetching staff with ID:", id)
        staff_list = await _services.get_one_staff(staff_id=id, db=db)
        print("Staff list:", staff_list)
        if staff_list is None:
            raise HTTPException(status_code=404, detail="Staff not found")
        return staff_list

    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        print(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        print(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    
@router.get("/staff/count/{org_id}", response_model=_schemas.StaffCount, tags=["Staff APIs"])
async def get_all_staff(org_id: int, db: _orm.Session = Depends(get_db)):
    try:
    
        total_staffs = await _services.get_Total_count_staff(org_id, db)
        print("Staff list:", total_staffs)
        if total_staffs is None:
            raise HTTPException(status_code=404, detail="Staff not found")
        return {"total_staffs": total_staffs}
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        print(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        print(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
   

@router.put("/staff", response_model= _schemas.UpdateStaff ,tags=["Staff APIs"])
async def update_staff(staff_update: _schemas.UpdateStaff, db: _orm.Session = Depends(get_db)):
    try:
        updated_staff = await _services.update_staff(staff_update.id, staff_update, db)
        return updated_staff
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.delete("/staff/{id}", tags=["Staff APIs"])
async def delete_staff(id:int, db: _orm.Session = Depends(get_db)):
    try:
        
        return await _services.delete_staff(id, db)
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    
    
    
@router.get("/staff",tags=["Staff APIs"])
async def get_staff(
    org_id: int,
    filters: Annotated[_schemas.StaffFilterParams, Depends(_services.get_filters)] = None,
    db: _orm.Session = Depends(get_db)):
    try:
        
        staff = _services.get_filtered_staff(db=db,org_id=org_id,params=filters)
        return staff
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")



## Roles and Permissions
@router.post("/role", tags=["Roles and Permissions"])
async def create_role(role: _schemas.RoleCreate, db: _orm.Session = Depends(get_db)):
    try:
    
        await _services.check_role(role, db)
        new_role = await _services.create_role(role, db)
        print("New Role: ", new_role)
        return {
            "status_code": "201",
            "id": new_role.id,
            "message": "Role created successfully"
        }
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.put("/role", tags=["Roles and Permissions"])
async def edit_role(role: _schemas.RoleUpdate, db: _orm.Session = Depends(get_db)):
    try:
        
        print("Role: ", role)
        new_role = await _services.edit_role(role, db)
        print("New Role: ", new_role)
        return {
            "status_code": "201",
            "id": new_role.id,
            "message": "Role updated successfully"
        }
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")



@router.get("/role", tags=["Roles and Permissions"])#, response_model=List[_schemas.RoleRead], tags=["Roles and Permissions"])
async def get_roles(org_id: Optional[int] = None,role_id: Optional[int] = None, db: _orm.Session = Depends(get_db)):
    try:
        
        if not org_id and not role_id:
            raise HTTPException(status_code=400, detail="Provide either org_id or role_id")
        if org_id and role_id:
            raise HTTPException(status_code=400, detail="Provide either org_id or role_id, not both")
        if org_id:
            roles = await _services.get_all_roles(org_id, db)
        elif role_id:
            roles = await _services.test_get_role(role_id, db)
        return roles
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.delete("/role", tags=["Roles and Permissions"])
async def delete_role(role_id: int, db: _orm.Session = Depends(get_db)):
    try:
        
        deleted_role = await _services.delete_role(role_id, db)
        if not deleted_role:
            raise HTTPException(status_code=404, detail="Role not found")
        return {
            "status_code": "200",
            "message": "Role deleted successfully"
        }
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.get("/role/resource", response_model = List[_schemas.ResourceRead], tags=["Roles and Permissions"])
async def get_resources(db: _orm.Session = Depends(get_db)):
    try:
        
        resources = await _services.get_all_resources(db)
        return resources
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
