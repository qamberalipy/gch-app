from datetime import datetime
from typing import Optional, Tuple, List
import logging
import sqlalchemy.orm as _orm
from fastapi import HTTPException

import app.user.models as _models
import app.Shared.schema as _schemas
import app.core.db.session as _database
from app.Shared import helpers as _helpers

logger = logging.getLogger("uvicorn.error")

# DB dependency
def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Helpers ---

def get_user_by_email(db: _orm.Session, email: str) -> Optional[_models.User]:
    return db.query(_models.User).filter(_models.User.email == email, _models.User.is_deleted == False).first()

def save_otp(db: _orm.Session, email: str, otp: str, purpose: str = "verify") -> _models.OTP:
    # Invalidate previous OTPs for this purpose
    previous_otps = db.query(_models.OTP).filter(
        _models.OTP.email == email, 
        _models.OTP.purpose == purpose, 
        _models.OTP.used == False
    ).all()
    for prev in previous_otps:
        prev.used = True
    
    record = _models.OTP(email=email, otp=otp, purpose=purpose)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def verify_otp(db: _orm.Session, email: str, otp_value: str, purpose: str = "verify", expiry_seconds: int = 15 * 60) -> bool:
    record = (
        db.query(_models.OTP)
        .filter(_models.OTP.email == email, _models.OTP.purpose == purpose, _models.OTP.used == False)
        .order_by(_models.OTP.created_at.desc())
        .first()
    )
    if not record:
        return False
    age = datetime.utcnow() - record.created_at
    if record.otp == otp_value and age.total_seconds() <= expiry_seconds:
        record.used = True
        db.add(record)
        db.commit()
        return True
    return False

# --- Core Auth Logic ---

def login_with_email(db: _orm.Session, email: str, password: str) -> Tuple[_models.User, str, str]:
    user = get_user_by_email(db, email)
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Check Account Status
    if user.account_status != _models.AccountStatus.active:
        raise HTTPException(status_code=403, detail=f"Account is {user.account_status}")

    if not user.password_hash or not user.verify_password(password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Generate Tokens
    access_token = _helpers.create_access_token(user.id)
    refresh_token = _helpers.create_refresh_token(user.id)
    
    # Save Refresh Token
    rt = _models.RefreshToken(user_id=user.id, token=refresh_token)
    db.add(rt)
    
    # Update Stats
    user.last_login = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user, access_token, refresh_token

def create_user_by_admin(db: _orm.Session, payload: _schemas.CreateUserReq) -> _models.User:
    """
    Admin/Manager creates a user directly.
    """
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = _models.User(
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        gender=payload.gender, # Ensure 'gender' column exists in models.py
        phone=payload.phone,
        city=payload.city,
        country_id=payload.country_id,
        timezone=payload.timezone,
        is_onboarded=False, # User must setup/change pass on first login if required
        account_status=_models.AccountStatus.active
    )
    
    new_user.set_password(payload.password)
    
    if payload.dob:
        # Simple string to date conversion
        try:
            new_user.dob = datetime.strptime(payload.dob, "%Y-%m-%d").date()
        except ValueError:
            pass # Or raise error

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- Password Management ---

def reset_password_using_otp(db: _orm.Session, email: str, otp_value: str, new_password: str):
    if not verify_otp(db, email, otp_value, purpose="reset"):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.set_password(new_password)
    db.add(user)
    db.commit()
    return True

# --- Token Mgmt ---

def refresh_access_token(db: _orm.Session, refresh_token: str) -> str:
    record = db.query(_models.RefreshToken).filter(
        _models.RefreshToken.token == refresh_token,
        _models.RefreshToken.revoked == False
    ).first()
    
    if not record:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    payload = _helpers.decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user_id = payload.get("sub")
    return _helpers.create_access_token(int(user_id))

def logout_user(db: _orm.Session, refresh_token: Optional[str] = None) -> bool:
    if refresh_token:
        record = db.query(_models.RefreshToken).filter(_models.RefreshToken.token == refresh_token).first()
        if record:
            record.revoked = True
            db.add(record)
            db.commit()
    return True