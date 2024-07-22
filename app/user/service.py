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
    staff_detail = db.query(_models.User).filter( _models.User.is_deleted == False and _models.User.id==staff_id).first()
    return staff_detail

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
        _models.User.id,
        _models.User.own_staff_id,
        _models.User.first_name,
        _models.User.last_name,
        _models.User.email,
        _models.User.mobile,
        _models.User.role_id,
        _models.User.profile_img,
        _models.Role.name.label("role_name")    
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
            _models.User.mobile.ilike(search_pattern),
            _models.User.profile_img.ilike(search_pattern),
            _models.User.notes.ilike(search_pattern),
            _models.User.city.ilike(search_pattern),
            _models.User.zipcode.ilike(search_pattern),
            _models.User.address_1.ilike(search_pattern),
            _models.User.address_2.ilike(search_pattern)
        ))

    staff = query.all()

    return [
        _schemas.StaffFilterRead(
            id=st.id,
            own_staff_id=st.own_staff_id,
            first_name=st.first_name,
            last_name=st.last_name,
            email=st.email,
            mobile=st.mobile,
            role_id=st.role_id,
            role_name=st.role_name,
            profile_img=st.profile_img
        )
        for st in staff
    ]


async def create_role(role: _schemas.RoleCreate, db: _orm.Session = _fastapi.Depends(get_db)):
    db_role = _models.Role(
        name=role.name,
        org_id=role.org_id
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    db_permission = _models.Permission(
        resource_id=role.resource_id,
        role_id=db_role.id,
        access_type=role.access_type,
        created_by=role.created_by,
        created_at=role.created_at
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_role