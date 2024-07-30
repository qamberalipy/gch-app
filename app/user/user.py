from typing import Dict, List, Optional
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.exc import IntegrityError, DataError
import app.user.schema as _schemas
import sqlalchemy.orm as _orm
import app.user.models as _models
import app.user.service as _services
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

@router.post("/register/admin")
async def register_user(user: _schemas.UserCreate, db: _orm.Session = Depends(get_db)):
    print("Here 1", user.email, user.password, user.first_name)
    db_user = await _services.get_user_by_email(user.email, db)
    print(f"User: {db_user}")
    print("Here 2")
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    organization_details = _schemas.OrganizationCreate(org_name=user.org_name)
    organization = await _services.create_organization(organization_details, db)

    user_data = user.dict()
    user_data['org_id'] = organization.id
    user_data.pop('org_name')

    user_register = _schemas.UserRegister(**user_data, created_at=datetime.datetime.utcnow())
    new_user = await _services.create_user(user_register, db)
    
    return new_user


@router.post("/login")
async def login(user: _schemas.GenerateUserToken,db: _orm.Session = Depends(get_db)):
    
    if user.email in lockout_expiry and datetime.datetime.now() < lockout_expiry[user.email]:
        raise HTTPException(status_code=403, detail="Account locked. Try again later.")

    authenticated_user = await _services.authenticate_user(user.email, user.password, db)
    if not authenticated_user:
        login_attempts[user.email] = login_attempts.get(user.email, 0) + 1

        if login_attempts[user.email] >= MAX_ATTEMPTS:
            # Lock the account if maximum attempts are reached
            lockout_expiry[user.email] = datetime.now() + LOCKOUT_TIME
            raise HTTPException(status_code=403, detail="Account locked. Try again later.")

        raise HTTPException(status_code=401, detail="Invalid email or password")

    login_attempts[user.email] = 0
    # token = await _services.create_token(authenticated_user)
    token = _helpers.create_token(authenticated_user, "User")
    user_data = await _services.get_alluser_data(email=user.email, db=db)
    return {
        "user": user_data,
        "token": token
    }


@router.post("/test_token")
async def test_token(
        token: str,
        db: _orm.Session = Depends(get_db)
    ):
    print("Token 1: ", token)
    payload = _helpers.verify_jwt(token, "User")
    return payload

@router.post("/refresh_token", tags=["Auth"])
async def refresh_token(refresh_token: str = Header(None, alias="refresh_token")):
    return _helpers.refresh_jwt(refresh_token)
    

@router.get("/get_all_countries/", response_model=List[_schemas.CountryRead])
async def read_countries(db: _orm.Session = Depends(get_db)):
    countries = _services.get_all_countries(db=db)
    if not countries:
        raise HTTPException(status_code=404, detail="No countries found")
    return countries


@router.get("/get_all_sources/", response_model=List[_schemas.SourceRead])
async def read_sources(db: _orm.Session = Depends(get_db)):
    sources = _services.get_all_sources(db=db)
    if not sources:
        raise HTTPException(status_code=404, detail="No sources found")
    return sources


@router.get("/get_staff",response_model=List[_schemas.getStaff],tags=["Staff APIs"])
async def get_staff(org_id:int, db: _orm.Session= Depends(get_db), authorization: str = Header(None)):
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing access token")

    _helpers.verify_jwt(authorization, "User")
    filtered_users =  db.query(_models.User.org_id,_models.User.id,_models.User.first_name).filter(_models.User.org_id == org_id, _models.User.is_deleted == False).all()
    return filtered_users


@router.get("/get_privileges",response_model=List[_schemas.getPrivileges],tags=["Staff APIs"])
async def get_privileges(org_id:int, db: _orm.Session= Depends(get_db), authorization: str = Header(None)):
    
    if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

    _helpers.verify_jwt(authorization, "User")
    organization_roles=  db.query(_models.Role).filter(_models.Role.org_id == org_id and _models.Role.is_deleted==False).all()
    return organization_roles


@router.post("/staff/staffs", response_model=_schemas.ReadStaff, tags=["Staff APIs"])
async def register_staff(staff: _schemas.CreateStaff, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        
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


@router.get("/staff/staffs", response_model=_schemas.ReadStaff, tags=["Staff APIs"])
async def get_all_staff(staff_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")

        print("Fetching staff with ID:", staff_id)
        staff_list = await _services.get_one_staff(staff_id, db)
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
    
@router.get("/staff/staffs/getTotalStaff", response_model=_schemas.StaffCount, tags=["Staff APIs"])
async def get_all_staff(org_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")

        print("Fetching staff with ID:", org_id)
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
    


@router.put("/staff/staffs", response_model=_schemas.ReadStaff, tags=["Staff APIs"])
async def update_staff(staff_update: _schemas.UpdateStaff, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        
        updated_staff = await _services.update_staff(staff_update.id, staff_update, db)
        return updated_staff
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.delete("/staff/staffs", tags=["Staff APIs"])
async def delete_staff(staff_delete: _schemas.DeleteStaff, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        
        return await _services.delete_staff(staff_delete.id, db)
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    
    
    
@router.get("/staff/staffs/getAll", response_model=List[_schemas.StaffFilterRead], tags=["Staff APIs"])
async def get_staff(
    org_id: int,
    request: Request,
    db: _orm.Session = Depends(get_db),
    authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        params = {
            "org_id": org_id,
            "search_key": request.query_params.get("search_key"),
            "staff_name": request.query_params.get("staff_name"),
            "role_name": request.query_params.get("role_name"),
        }
        staff = _services.get_filtered_staff(db=db, params=_schemas.StaffFilterParams(**params))
        return staff
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")



## Roles and Permissions
@router.post("/role", tags=["Roles and Permissions"])
async def create_role(role: _schemas.RoleCreate, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
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
async def edit_role(role: _schemas.RoleUpdate, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        print("Authorization: ", authorization)
        _helpers.verify_jwt(authorization, "User")
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



@router.get("/role", response_model=List[_schemas.RoleRead], tags=["Roles and Permissions"])
async def get_roles(org_id: Optional[int] = None, role_id: Optional[int] = None, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        if not org_id and not role_id:
            raise HTTPException(status_code=400, detail="Provide either org_id or role_id")
        if org_id:
            print("In org")
            roles = await _services.get_all_roles(org_id, db)
        elif role_id:
            print("In role")
            roles = await _services.get_role(role_id, db)

        return roles
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.delete("/role", tags=["Roles and Permissions"])
async def delete_role(role_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
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
async def get_resources(db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        resources = await _services.get_all_resources(db)
        return resources
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
