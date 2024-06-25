import jwt
import sqlalchemy.orm as _orm
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

# Load environment variables
JWT_SECRET = os.getenv("JWT_SECRET")
oauth2schema = _security.OAuth2PasswordBearer("/token")


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
        username=user.username, 
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
    token = jwt.encode(user_dict, JWT_SECRET, algorithm="HS256")
    return dict(access_token=token, token_type="bearer")

async def get_current_user(db: _orm.Session = _fastapi.Depends(get_db), token: str = _fastapi.Depends(oauth2schema)):
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
    return db.query(models.User).filter(models.User.email == email).first()


async def create_client(client: _schemas.RegisterClient, db: _orm.Session = _fastapi.Depends(get_db)):
    db_client = models.Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

async def create_client_organization(client_organization: _schemas.CreateClient_Organization,  db: _orm.Session = _fastapi.Depends(get_db)):
    db_client_organization = models.ClientOrganization(**client_organization.dict())
    db.add(db_client_organization)
    db.commit()
    db.refresh(db_client_organization)
    return db_client_organization

async def create_client_membership(client_membership: _schemas.CreateClient_membership,  db: _orm.Session = _fastapi.Depends(get_db)):
    db_client_membership = models.ClientMembership(**client_membership.dict())
    db.add(db_client_membership)
    db.commit()
    db.refresh(db_client_membership)
    return db_client_membership

async def create_client_coach(client_coach: _schemas.CreateClient_coach,  db: _orm.Session = _fastapi.Depends(get_db)):
    db_client_coach = models.ClientCoach(**client_coach.dict())
    db.add(db_client_coach)
    db.commit()
    db.refresh(db_client_coach)
    return db_client_coach



async def create_bank_account(bank_account:_schemas.BankAccountCreate,db: _orm.Session = _fastapi.Depends(get_db)):
    db_bank_account = models.BankAccount(**bank_account.dict())
    db.add(db_bank_account)
    db.commit()
    db.refresh(db_bank_account)
    return db_bank_account

def get_client_by_email(email_address,db):
    client = db.query(_models.Client).filter(_models.Client.email_address == email_address).first()
    print("client",client.email_address,client.wallet_address)
    if not client:
        return None
    else:
        return client
    
async def authenticate_client(email_address: str,db: _orm.Session = _fastapi.Depends(get_db)):
    client = get_client_by_email(email_address , db)
      
    if not client:
        return False
   
    return client
        
async def authenticate_user(email: str, password: str, db: _orm.Session):
    # Authenticate a user
    user = await get_user_by_email(email=email, db=db)

    if not user:
        return False
   
    if not user.verify_password(password):
        return False

    return user