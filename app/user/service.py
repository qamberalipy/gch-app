from datetime import date,datetime
from typing import List
import jwt
from sqlalchemy import desc, func, or_
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.user.schema as _schemas
import app.user.models as _models
import random
import json
import pika
import time
import os
import bcrypt as _bcrypt
from . import models, schema
import logging
import pydantic
# Load environment variables

logger = logging.getLogger("uvicorn.error")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRY = os.getenv("JWT_EXPIRY")

oauth2schema = _security.OAuth2PasswordBearer(tokenUrl="api/login")
def create_database():
    # Create database tables
    return _database.Base.metadata.create_all(bind=_database.engine)

def get_db():
    # Dependency to get a database session
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_jwt(token: str):
    # Verify a JWT token
    credentials_exception = _fastapi.HTTPException(
        status_code=_fastapi.status.HTTP_401_UNAUTHORIZED,
        detail="Token Expired or Invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = token.split("Bearer ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print("Time Difference", time.time() - payload["token_time"])
        if time.time() - payload["token_time"] > JWT_EXPIRY:
            print("Token Expired")
            raise credentials_exception

        return payload
    except:
        raise credentials_exception

def hash_password(password):
    # Hash a password
    return _bcrypt.hashpw(password.encode('utf-8'), _bcrypt.gensalt()).decode('utf-8')

async def get_user_by_email(email: str, db: _orm.Session):
    # Retrieve a user by email from the database
    print("Email: ", email)
    return db.query(_models.User).filter(_models.User.email == email).first()

async def create_user(user: _schemas.UserRegister, db: _orm.Session):
    try:
        valid = _email_check.validate_email(user.email)
        email = valid.email
    except _email_check.EmailNotValidError:
        raise _fastapi.HTTPException(status_code=400, detail="Please enter a valid email")

    hashed_password = hash_password(user.password)
    user_obj = _models.User(
        email=email, 
        first_name=user.first_name, 
        password=hashed_password,
        org_id=user.org_id
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj

async def create_organization(organization: _schemas.OrganizationCreate, db: _orm.Session = _fastapi.Depends(get_db)):
    org = _models.Organization(org_name=organization.org_name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

async def create_token(user: _models.User):
    # Create a JWT token for authentication
    user_obj = _schemas.User.from_orm(user)
    user_dict = user_obj.dict()
    print(user_dict)
    del user_dict["date_created"]
    user_dict['token_time'] = time.time()
    print("JWT_SECRET", JWT_SECRET)
    print("User Dict: ", user_dict)
    token = jwt.encode(user_dict, JWT_SECRET, algorithm="HS256")
    return dict(access_token=token, token_type="bearer")

async def get_current_user(token: str, db: _orm.Session = _fastapi.Depends(get_db)):
    # Get the current authenticated user from the JWT token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = db.query(_models.User).get(payload["id"])
    except:
        raise _fastapi.HTTPException(status_code=401, detail="Invalid Email or Password")
    return _schemas.UserSchema.from_orm(user)

def generate_otp():
    # Generate a random OTP
    return str(random.randint(100000, 999999))

async def get_user_by_email(email: str, db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(models.User).filter(models.User.email == email).first()

async def get_alluser_data(email: str, db: _orm.Session = _fastapi.Depends(get_db)):
    # Retrieve a user by email from the database
    result = (
        db.query(_models.User, _models.Organization.org_name)
        .join(_models.Organization, _models.User.org_id == _models.Organization.id)
        .filter(_models.User.email == email)
        .first()
    )
    
    if result:
        user, org_name = result
        return {
            "id": user.id,
            "first_name": user.first_name,
            "email": user.email,
            "date_created": user.created_at,
            "org_id": user.org_id,
            "org_name": org_name,
            "is_deleted": user.is_deleted
        }
    return None

async def create_bank_account(bank_account:_schemas.BankAccountCreate,db: _orm.Session = _fastapi.Depends(get_db)):
    db_bank_account = models.BankAccount(**bank_account.dict())
    db.add(db_bank_account)
    db.commit()
    db.refresh(db_bank_account)
    return db_bank_account

async def create_staff(staff: _schemas.CreateStaff, db: _orm.Session = _fastapi.Depends(get_db)):
    staff_data = staff.dict()
    try:
       _email_check.validate_email(staff_data.get('email'))

    except _email_check.EmailNotValidError:
        raise _fastapi.HTTPException(status_code=400, detail="Please enter a valid email")

    print(staff_data.pop("send_invitation"))
    db_staff = _models.User(**staff_data)
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff
        
async def authenticate_user(email: str, password: str, db: _orm.Session):
    # Authenticate a user
    user = await get_user_by_email(email=email, db=db)

    if not user:
        return False
   
    if not user.verify_password(password):
        return False

    return user


def get_all_countries( db: _orm.Session):
    return db.query(_models.Country).filter(_models.Country.is_deleted == False).all()

def get_all_sources( db: _orm.Session):
    return db.query(_models.Source).all()

async def get_one_staff(staff_id: int, db: _orm.Session):
    staff_detail = db.query(
        *models.User.__table__.columns,_models.Role.name.label("role_name")
        ).join(
            _models.Role, _models.User.role_id == _models.Role.id
        ).filter(
            _models.User.is_deleted == False,
            _models.User.id == staff_id
    ).first()
    print(staff_detail)
    if staff_detail:
        return staff_detail
    else :
        return None
    

async def update_staff(staff_id: int, staff_update: _schemas.UpdateStaff, db: _orm.Session):
    staff = db.query(_models.User).filter(_models.User.id == staff_id).first()
    if staff is None:
        raise _fastapi.HTTPException(status_code=404, detail="Staff not found")
    
    update_data = staff_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(staff, key, value)
    
    staff.updated_at = datetime.now()
    db.commit()
    db.refresh(staff)
    return staff


async def delete_staff(staff_id: int, db: _orm.Session):
    staff = db.query(_models.User).filter(_models.User.id == staff_id).first()
    if staff is None:
        raise _fastapi.HTTPException(status_code=404, detail="Staff not found")
    
    staff.is_deleted = True
    db.commit()
    return {"detail": "Staff deleted successfully"}

def get_filtered_staff(
    db: _orm.Session,
    params: _schemas.StaffFilterParams
) -> List[_schemas.StaffFilterRead]:
    query = db.query(
        *models.User.__table__.columns,_models.Role.name.label("role_name")    
    ).join(
        _models.Role, _models.User.role_id == _models.Role.id
    ).filter(
        _models.User.org_id == params.org_id,
        _models.User.is_deleted == False
    ).order_by(
        desc(_models.User.created_at))

    if params.staff_name:
        query = query.filter(or_(
            _models.User.first_name.ilike(f"%{params.staff_name}%"),
            _models.User.last_name.ilike(f"%{params.staff_name}%")
        ))

    if params.role_name:
        query = query.filter(_models.Role.name.ilike(f"%{params.role_name}%"))

    if params.search_key:
        search_pattern = f"%{params.search_key}%"
        query = query.filter(or_(
            _models.User.own_staff_id.ilike(search_pattern),
            _models.User.first_name.ilike(search_pattern),
            _models.User.last_name.ilike(search_pattern),
            _models.User.email.ilike(search_pattern),
            _models.User.mobile_number.ilike(search_pattern),
            _models.User.profile_img.ilike(search_pattern),
            _models.User.notes.ilike(search_pattern),
            _models.User.city.ilike(search_pattern),
            _models.User.zipcode.ilike(search_pattern),
            _models.User.address_1.ilike(search_pattern),
            _models.User.address_2.ilike(search_pattern)
        ))

    staff = query.all()

    return staff
    

async def check_role(role: _schemas.RoleCreate, db: _orm.Session = _fastapi.Depends(get_db)):
    ch_role = db.query(_models.Role).filter(_models.Role.name == role.name, _models.Role.org_id == role.org_id).first()
    
    if ch_role is not None:
        raise _fastapi.HTTPException(status_code=400, detail="Role already exists")

    if len(role.resource_id) != len(role.access_type):
        raise _fastapi.HTTPException(status_code=400, detail="Resource ID and Access Type should be equal")

    return True

async def create_role(role: _schemas.RoleCreate, db: _orm.Session = _fastapi.Depends(get_db)):
    db_role = _models.Role(
        name=role.name,
        org_id=role.org_id,
        is_deleted=0
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)

    for i in range(len(role.resource_id)):
        db_permission = _models.Permission(
            role_id=db_role.id,
            resource_id=role.resource_id[i],
            access_type=role.access_type[i],
            created_by=role.created_by,
            updated_by=role.created_by,
            is_deleted=0
        )
        db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_role


async def get_all_roles(org_id: int, db: _orm.Session):
    return db.query(_models.Role.name.label("role_name"), _models.Role.id.label("role_id"))\
        .filter(_models.Role.is_deleted == False, _models.Role.org_id == org_id).all()

async def temp_get_role(role_id: int, db: _orm.Session):
    role = db.query(_models.Role).filter(_models.Role.id == role_id, _models.Role.is_deleted == False).first()
    if role is None:
        raise _fastapi.HTTPException(status_code=404, detail="Role not found")
    
    permissions = db.query(_models.Resource.name.label("resource_name"), _models.Permission.access_type, _models.Role.org_id, 
        _models.Role.status, _models.Permission.id.label("permission_id"), _models.Role.id.label("role_id"), _models.Resource.code, 
        _models.Resource.link, _models.Resource.icon, _models.Resource.is_parent, _models.Resource.parent)\
        .join(_models.Permission, _models.Resource.id == _models.Permission.resource_id)\
        .join(_models.Role, _models.Permission.role_id == _models.Role.id)\
        .filter(_models.Permission.role_id == role_id, _models.Permission.is_deleted == False).all()

    return permissions


from collections import defaultdict

async def test_get_role(role_id: int, db: _orm.Session):
    role = db.query(_models.Role).filter(_models.Role.id == role_id, _models.Role.is_deleted == False).first()
    if role is None:
        raise _fastapi.HTTPException(status_code=404, detail="Role not found")
  
    permissions = db.query(
        _models.Resource
    ).options(
        _orm.joinedload(_models.Resource.children)
    ).filter(
        # _models.Resource.is_parent == True,
        _models.Permission.role_id == role_id,
        _models.Permission.is_deleted == False,
    ).all()
    
    permissions = [p for p in permissions if p.is_root]

    # permission_pydantic = pydantic.parse_obj_as(List[_schemas.RoleRead], permissions)

    return permissions


async def get_role(role_id: int, db: _orm.Session):
    role = db.query(_models.Role).filter(_models.Role.id == role_id, _models.Role.is_deleted == False).first()
    if role is None:
        raise _fastapi.HTTPException(status_code=404, detail="Role not found")
    
    permissions = db.query(
        _models.Resource.name.label("resource_name"),
        _models.Permission.access_type,
        _models.Role.org_id,
        _models.Role.status,
        _models.Permission.id.label("permission_id"),
        _models.Role.id.label("role_id"),
        _models.Role.name.label("role_name"),
        _models.Resource.code,
        _models.Resource.link,
        _models.Resource.icon,
        _models.Resource.is_parent,
        _models.Resource.parent
    ).join(
        _models.Permission, _models.Resource.id == _models.Permission.resource_id
    ).join(
        _models.Role, _models.Permission.role_id == _models.Role.id
    ).filter(
        _models.Permission.role_id == role_id,
        _models.Permission.is_deleted == False
    ).all()

    # Create a dictionary to store roles by their code
    resource_dict = {p.code: _schemas.RoleRead(**p._asdict(), subRows=[]) for p in permissions if p.code is not None}

    # Include parent roles in resource_dict if they are missing
    for perm in permissions:
        if perm.parent and perm.parent not in resource_dict:
            parent_role = db.query(
                _models.Resource.name.label("resource_name"),
                _models.Role.org_id,
                _models.Role.status,
                _models.Role.id.label("role_id"),
                _models.Resource.code,
                _models.Resource.link,
                _models.Resource.icon,
                _models.Resource.is_parent,
                _models.Resource.parent
            ).filter(
                _models.Resource.code == perm.parent,
                _models.Role.id == role_id
            ).first()
            if parent_role:
                resource_dict[perm.parent] = _schemas.RoleRead(
                    resource_name=parent_role.resource_name,
                    role_id=parent_role.role_id,
                    org_id=parent_role.org_id,
                    status=parent_role.status,
                    permission_id=None,
                    access_type=None,
                    is_parent=parent_role.is_parent,
                    parent=parent_role.parent,
                    code=parent_role.code,
                    link=parent_role.link,
                    icon=parent_role.icon,
                    is_deleted=False,
                    subRows=[]
                )

    # Create a dictionary to store parent-child relationships
    children_map = defaultdict(list)
    for perm in permissions:
        if perm.parent and perm.parent in resource_dict:
            children_map[perm.parent].append(_schemas.RoleRead(**perm._asdict(), subRows=[]))

    # Assign children to their respective parents
    for code, role in resource_dict.items():
        if code in children_map:
            role.subRows.extend(children_map[code])

    # Collect all roles (root roles and their children)
    all_roles = []
    for code, role in resource_dict.items():
        if role.parent is None:
            all_roles.append(role)

    return all_roles


async def edit_role(role: _schemas.RoleUpdate, db: _orm.Session):
    db_role = db.query(_models.Role).filter(_models.Role.id == role.id).first()
    if db_role is None:
        raise _fastapi.HTTPException(status_code=404, detail="Role not found")
    
    update_data = role.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_role, key, value)
    
    db_role.updated_at = datetime.now()
    db.commit()
    db.refresh(db_role)

    if role.resource_id is None or role.access_type is None:
        return db_role

    if len(role.resource_id) != len(role.access_type):
        raise _fastapi.HTTPException(status_code=400, detail="Resource ID and Access Type should be equal")
    

    permissions = db.query(_models.Permission).filter(_models.Permission.role_id == role.id and _models.Permission.resource_id not in role.resource_id).all()
    print("Check Permissions: ", permissions)
    for permission in permissions:
        permission.is_deleted = 1
    db.commit()

    for i in range(len(role.resource_id)):
        db_permission = db.query(_models.Permission).filter(_models.Permission.role_id == role.id, _models.Permission.resource_id == role.resource_id[i]).first()
        if db_permission is None:
            db_permission = _models.Permission(
                role_id=role.id,
                resource_id=role.resource_id[i],
                access_type=role.access_type[i],
                created_by=role.created_by,
                updated_by=role.created_by,
                is_deleted=0
            )
            db.add(db_permission)
        else:
            print("Here: ")
            db_permission.is_deleted = 0
            db_permission.access_type = role.access_type[i]
            db_permission.updated_at = datetime.now()
        db.commit()
    db.refresh(db_permission)
    return db_role

async def delete_role(role_id: int, db: _orm.Session):
    print("Role ID: ", role_id)
    role = db.query(_models.Role).filter(_models.Role.id == role_id, _models.Role.is_deleted == False).first()
    print("Role: ", role)
    if role is None:
        raise _fastapi.HTTPException(status_code=404, detail="Role not found")
    
    role.is_deleted = 1
    role.status = 0
    db.commit()

    permissions = db.query(_models.Permission).filter(_models.Permission.role_id == role_id).all()
    for permission in permissions:
        permission.is_deleted = 1
    db.commit()
    return {"detail": "Role deleted successfully"}

async def get_all_resources(db: _orm.Session):
    return db.query(_models.Resource).filter(_models.Resource.is_deleted == False).all()

async def get_Total_count_staff(org_id: int, db: _orm.Session = _fastapi.Depends(get_db)) -> int:
    total_staffs = db.query(func.count(models.User.id)).filter(
        _models.User.org_id == org_id,
        _models.User.is_deleted == False
        
    ).scalar()
    print(total_staffs)
    return total_staffs
