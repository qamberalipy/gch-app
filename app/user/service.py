from datetime import date
import jwt
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