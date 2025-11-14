from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
import os
import logging

import sqlalchemy.orm as _orm
from fastapi import HTTPException

import app.user.models as _models
import app.user.schema as _schemas
import app.core.db.session as _database
from app.Shared import helpers as _helpers

logger = logging.getLogger("uvicorn.error")

# environment / defaults
ACCESS_TOKEN_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "900"))

# DB dependency
def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Basic helpers for DB queries
def check_email_exists(db: _orm.Session, email: str) -> bool:
    return db.query(_models.User).filter(_models.User.email == email, _models.User.is_deleted == False).first() is not None


def check_username_available(db: _orm.Session, username: str) -> bool:
    if not username:
        return False
    return db.query(_models.User).filter(_models.User.username == username, _models.User.is_deleted == False).first() is None


def save_otp(db: _orm.Session, email: str, otp: str, purpose: str = "verify") -> _models.OTP:
    record = _models.OTP(email=email, otp=otp, purpose=purpose)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_latest_otp(db: _orm.Session, email: str, purpose: str = "verify") -> Optional[_models.OTP]:
    return (
        db.query(_models.OTP)
        .filter(_models.OTP.email == email, _models.OTP.purpose == purpose, _models.OTP.used == False)
        .order_by(_models.OTP.created_at.desc())
        .first()
    )


def mark_otp_used(db: _orm.Session, otp_record: _models.OTP) -> None:
    otp_record.used = True
    db.add(otp_record)
    db.commit()


def verify_otp(db: _orm.Session, email: str, otp_value: str, purpose: str = "verify", expiry_seconds: int = 15 * 60) -> bool:
    record = get_latest_otp(db, email, purpose)
    if not record:
        return False
    age = datetime.utcnow() - record.created_at
    if record.otp == otp_value and age.total_seconds() <= expiry_seconds:
        mark_otp_used(db, record)
        return True
    return False


# ----- Auth flows -----
def register_user(db: _orm.Session, payload: _schemas.RegisterReq) -> Tuple[_models.User, str, str]:
    if check_email_exists(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    if payload.username and not check_username_available(db, payload.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user = _models.User(
        email=payload.email,
        username=payload.username,
        profile_type_id=payload.profile_type_id,
        plan_type_id=payload.plan_type_id,
        auth_provider=payload.auth_provider or "local",
        google_id=payload.google_id,
        is_verified=False if (payload.auth_provider or "local") == "local" else True,
    )

    if payload.password and payload.auth_provider == "local":
        user.set_password(payload.password)

    db.add(user)
    db.commit()
    db.refresh(user)

    access_payload = {"sub": {"user_id": user.id}}
    access_token = _helpers.create_access_token(access_payload)
    refresh_token = _helpers.create_refresh_token(access_payload)

    # persist refresh token
    rt = _models.RefreshToken(user_id=user.id, token=refresh_token)
    db.add(rt)
    db.commit()

    return user, access_token, refresh_token


def login_with_email(db: _orm.Session, email: str, password: str) -> Tuple[_models.User, str, str]:
    user = db.query(_models.User).filter(_models.User.email == email, _models.User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not user.password_hash:
        raise HTTPException(status_code=400, detail="Account does not have a password; use social login")

    if not user.verify_password(password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_payload = {"sub": {"user_id": user.id}}
    access_token = _helpers.create_access_token(access_payload)
    refresh_token = _helpers.create_refresh_token(access_payload)

    rt = _models.RefreshToken(user_id=user.id, token=refresh_token)
    db.add(rt)
    db.commit()

    # update last_login
    user.last_login = datetime.utcnow()
    db.add(user)
    db.commit()

    return user, access_token, refresh_token


def login_with_google(db: _orm.Session, id_token: str) -> Tuple[_models.User, str, str]:
    # For production, verify Google token signature with Google's library.
    # Here we decode & trust token payload but ensure email exists.
    try:
        payload = _helpers.decode_token(id_token)
    except Exception:
        # try decode without verification (useful if frontend gives raw Google token) *not recommended*
        import jwt
        try:
            payload = jwt.decode(id_token, options={"verify_signature": False})
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Google token")

    email = payload.get("email")
    google_sub = payload.get("sub")
    if not email:
        raise HTTPException(status_code=400, detail="Google token must contain email")

    user = db.query(_models.User).filter(
        (_models.User.email == email) | (_models.User.google_id == google_sub)
    ).first()

    if not user:
        username = email.split("@")[0]
        user = _models.User(
            email=email,
            username=username,
            auth_provider=_models.AuthProvider.google,
            google_id=google_sub,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_payload = {"sub": {"user_id": user.id}}
    access_token = _helpers.create_access_token(access_payload)
    refresh_token = _helpers.create_refresh_token(access_payload)

    rt = _models.RefreshToken(user_id=user.id, token=refresh_token)
    db.add(rt)
    db.commit()

    return user, access_token, refresh_token


def _verify_refresh_token_record(db: _orm.Session, token: str) -> Optional[_models.RefreshToken]:
    return db.query(_models.RefreshToken).filter(_models.RefreshToken.token == token, _models.RefreshToken.revoked == False).first()


def refresh_access_token(db: _orm.Session, refresh_token: str) -> str:
    record = _verify_refresh_token_record(db, refresh_token)
    if not record:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    payload = _helpers.decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("sub", {}).get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload")

    access_payload = {"sub": {"user_id": user_id}}
    return _helpers.create_access_token(access_payload)


def revoke_refresh_token(db: _orm.Session, token: str) -> None:
    record = db.query(_models.RefreshToken).filter(_models.RefreshToken.token == token).first()
    if record:
        record.revoked = True
        db.add(record)
        db.commit()


def logout_user(db: _orm.Session, refresh_token: Optional[str] = None) -> bool:
    if refresh_token:
        revoke_refresh_token(db, refresh_token)
    return True


# ---- User queries ----
def get_user_by_email(db: _orm.Session, email: str) -> Optional[_models.User]:
    return db.query(_models.User).filter(_models.User.email == email, _models.User.is_deleted == False).first()


def get_user_by_id(db: _orm.Session, user_id: int) -> Optional[_models.User]:
    return db.query(_models.User).filter(_models.User.id == user_id, _models.User.is_deleted == False).first()


def get_all_countries(db: _orm.Session) -> List[_models.Country]:
    return db.query(_models.Country).filter(_models.Country.is_deleted == False).all()


def get_all_sources(db: _orm.Session) -> List[_models.Source]:
    return db.query(_models.Source).all()


def reset_password_using_otp(db: _orm.Session, email: str, otp_value: str, new_password: str):
    ok = verify_otp(db, email, otp_value, purpose="reset")
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.set_password(new_password)
    db.add(user)
    db.commit()
    return True
