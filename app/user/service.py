from datetime import date,datetime
from typing import List, Dict, Any, Optional
from typing import Annotated, List
import jwt
from sqlalchemy import asc, desc, func, or_, text
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
from collections import defaultdict
from app.user.models import StaffStatus
import smtplib
from email.mime.text import MIMEText
from fastapi import APIRouter, Depends, HTTPException, Header
from email.mime.multipart import MIMEMultipart
import sendgrid
# import resend
import app.Shared.helpers as _helpers
from sendgrid.helpers.mail import Mail, Email, To, Content

# Load environment variables

logger = logging.getLogger("uvicorn.error")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRY = os.getenv("JWT_EXPIRY")
LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL")
BASE_URL = os.getenv("BASE_URL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_SERVER = os.getenv("SMTP_SERVER")
# RESEND_API_KEY = os.getenv('RESEND_API_KEY')


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

def check_email_exists(db: _orm.Session, email: str) -> bool:
    return db.query(_models.User).filter(_models.User.email == email).first() is not None

def save_otp(db: _orm.Session, email: str, otp: str, purpose: str = "verify") -> _models.OTP:
    record = _models.OTP(email=email, otp=otp, purpose=purpose)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def mark_otp_used(db: _orm.Session, otp_record: _models.OTP) -> None:
    otp_record.used = True
    db.add(otp_record)
    db.commit()

def get_latest_otp(db: _orm.Session, email: str, purpose: str = "verify") -> Optional[_models.OTP]:
    return (
        db.query(_models.OTP)
        .filter(_models.OTP.email == email, _models.OTP.purpose == purpose, _models.OTP.used == False)
        .order_by(_models.OTP.created_at.desc())
        .first()
    )

def verify_otp(db: _orm.Session, email: str, otp_value: str, purpose: str = "verify") -> bool:
    record = get_latest_otp(db, email, purpose)
    if not record:
        return False
    age = datetime.utcnow() - record.created_at
    if record.otp == otp_value and age.total_seconds() <= 15 * 60:
        mark_otp_used(db, record)
      
        return True
    return False

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

def reset_password_using_otp(db: _orm.Session, email: str, otp_value: str, new_password: str):
    ok, _ = verify_otp(db, email, otp_value, purpose="reset")
    if not ok:
        raise ValueError("Invalid or expired OTP")

    user = db.query(_models.User).filter(_models.User.email == email).first()
    if not user:
        raise ValueError("User not found")

    user.password_hash = _helpers.hash_password(new_password)
    db.add(user)
    db.commit()
    return True

def login_with_email(db: _orm.Session, email: str, password: str):
    user = db.query(_models.User).filter(_models.User.email == email).first()
    if not user:
        raise ValueError("Invalid credentials")
    if not user.password_hash:
        raise ValueError("Account does not have a password; use social login")
    if not _helpers.verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")

    access = _helpers.create_access_token({"user_id": user.id})
    refresh = _helpers.create_refresh_token({"user_id": user.id})
    _store_refresh_token(db, user.id, refresh)
    return user, access, refresh

def login_with_google(db: _orm.Session, id_token: str):

    try:
        # decode without verifying Google's signature
        info = jwt.decode(id_token, options={"verify_signature": False})
    except Exception:
        raise ValueError("Invalid Google token format")

    email = info.get("email")
    google_sub = info.get("sub")  # Google unique user ID

    if not email:
        raise ValueError("Google token does not contain email")

    # check if user exists
    user = db.query(_models.User).filter(
        (_models.User.email == email) | (_models.User.google_id == google_sub)
    ).first()

    if not user:
        # register new user
        username = email.split("@")[0]
        user = _models.User(
            email=email,
            username=username,
            auth_provider="google",
            google_id=google_sub,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # generate tokens
    access = _helpers.create_access_token({"user_id": user.id})
    refresh = _helpers.create_refresh_token({"user_id": user.id})

    return user, access, refresh

def _store_refresh_token(db: _orm.Session, user_id: int, token: str) -> _models.RefreshToken:
    rt = _models.RefreshToken(user_id=user_id, token=token)
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


def _revoke_refresh_token(db: _orm.Session, token: str) -> None:
    r = db.query(_models.RefreshToken).filter(_models.RefreshToken.token == token).first()
    if r:
        r.revoked = True
        db.add(r)
        db.commit()

def refresh_access_token(db: _orm.Session, refresh_token: str):
    # verify stored refresh token
    record = _verify_refresh_token(db, refresh_token)
    if not record:
        raise ValueError("Invalid refresh token")
    # decode & generate new access
    payload = _helpers.decode_token(refresh_token)
    user_id = payload.get("user_id")
    if not user_id:
        raise ValueError("Invalid refresh token payload")
    access = _helpers.create_access_token({"user_id": user_id})
    return access


def _verify_refresh_token(db: _orm.Session, token: str) -> Optional[_models.RefreshToken]:
    r = db.query(_models.RefreshToken).filter(_models.RefreshToken.token == token, _models.RefreshToken.revoked == False).first()
    return r

def logout_user(db: _orm.Session, refresh_token: Optional[str] = None, access_token: Optional[str] = None):
    # revoke refresh token if provided. For access tokens, we rely on expiration.
    if refresh_token:
        _revoke_refresh_token(db, refresh_token)
    return True

def register_user(db: _orm.Session, payload: schema.RegisterReq, password_plain: Optional[str] = None):
    # If user exists with email raise
    if db.query(_models.User).filter(_models.User.email == payload.email).first():
        raise ValueError("Email already registered")

    if payload.username and db.query(_models.User).filter(_models.User.username == payload.username).first():
        raise ValueError("Username already taken")

    # create user object (fields must match your User model)
    # uses password hashing if provided, otherwise creates user with null password (for google)
    hashed = _helpers.hash_password(password_plain) if password_plain else None

    user = _models.User(
        email=payload.email,
        username=payload.username,
        password_hash=hashed,
        profile_type_id=payload.profile_type_id,
        plan_type_id=payload.plan_type_id,
        source_id=payload.source_id,
        auth_provider=payload.auth_provider or "local",
        google_id=payload.google_id,
        is_verified=True if payload.auth_provider != "local" else False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access = _helpers.create_access_token({"user_id": user.id})
    refresh = _helpers.create_refresh_token({"user_id": user.id})
    _store_refresh_token(db, user.id, refresh)
    return user, access, refresh

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
    return db.query(_models.User).filter(
        and_(
            _models.User.email == email,
            _models.User.is_deleted == False
        )
    ).first()

async def get_filtered_user_by_email(email: str, db: _orm.Session = _fastapi.Depends(get_db)):
    user =  db.query(models.User).filter(models.User.email == email, _models.User.is_deleted == False).first()
    if user:
        return user
    else: 
        raise HTTPException(status_code=404, detail="It appears there is no account with this email. Please verify the address provided.")


async def get_alluser_data(email: str, db: _orm.Session = _fastapi.Depends(get_db)):
    # Retrieve a user by email from the database
    result = (
        db.query(_models.User, _models.Organization.name)
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

    
        
async def authenticate_user(email: str, password: str, db: _orm.Session):
    # Authenticate a user
    user = await get_user_by_email(email=email, db=db)

    if not user:
       raise HTTPException(status_code=400, detail="No account found associated with the provided email.")

    if not user.verify_password(password):
        return False
    return user

def set_reset_token(id: int, email: str, token: str, db: _orm.Session):
    db.query(_models.User).filter(_models.User.id == id).filter(_models.User.email == email).update({"reset_token": token})
    db.commit()
    return token

def get_reset_token(id: int, db: _orm.Session):
    user = db.query(_models.User).filter(_models.User.id == id, _models.User.reset_token.isnot(None)).first()
    if user is None:
        return None

    return user.reset_token

def delete_reset_token(id: int, db: _orm.Session):
    db.query(_models.User).filter(_models.User.id == id).update({"reset_token": None})
    db.commit()

def get_all_countries( db: _orm.Session):
    return db.query(_models.Country).filter(_models.Country.is_deleted == False).all()

def get_all_sources( db: _orm.Session):
    return db.query(_models.Source).all()

