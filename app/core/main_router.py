import datetime
from typing import Dict, List
from urllib import request
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError
import app.Shared.helpers as _helpers
import sqlalchemy.orm as _orm

import app.Shared.schema as _schemas
from ..Shared.dependencies import get_db
import app.user.schema as _User_schemas
import app.user.models as _models
import app.user.service as _services
import app.core.db.session as _database
import json
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

router = APIRouter()
login_attempts: Dict[str, int] = {}
lockout_expiry: Dict[str, datetime.datetime] = {}
MAX_ATTEMPTS = 5
LOCKOUT_TIME = datetime.timedelta(minutes=30)


@router.get("/healthcheck", status_code=200)
def healthcheck():
    return JSONResponse(content=jsonable_encoder({"status": "Healthy yayy!"}))

@router.post("/auth/check-email",tags=["Auth"],)
async def check_email(email: _schemas.CheckEmailReq, db: _orm.Session = Depends(get_db)):
    if not _helpers.validate_email(email.email):
        raise HTTPException(status_code=400, detail="Incorrect email format")
    
    db_user = await _services.get_user_by_email(email.email,db)
    if db_user:
        return {"exists": True}
    return {"exists": False}

@router.post("/auth/send-otp", tags=["Auth"])
async def send_otp(email: _schemas.CheckEmailReq, db: _orm.Session = Depends(get_db)):
    if not _helpers.validate_email(email.email):
        raise HTTPException(status_code=400, detail="Incorrect email format")
    
    otp = _helpers.generate_otp()
    subject = "Password reset OTP"
    html_body = f"Your password reset OTP is: {otp}\nIf you did not request this, ignore."

    email_sent = _helpers.send_email(email.email, subject, html_body)
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send email")
    _services.save_otp(db, email.email, otp, purpose="verify")

    return JSONResponse(content={"message": f"An OTP has been sent to {email.email}. If you did not receive the email, please check your spam/junk mail folder."}, status_code=200)

@router.post("/auth/verify-otp", tags=["Auth"])
async def verify_otp(otp_request: _schemas.VerifyOtpReq, db: _orm.Session = Depends(get_db)):
    if not _helpers.validate_email(otp_request.email):
        raise HTTPException(status_code=400, detail="Incorrect email format")
    
    is_valid = _services.verify_otp(db, otp_request.email, str(otp_request.otp))
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    return JSONResponse(content={"message": "OTP verified successfully."}, status_code=200)

@router.post("/auth/forgot-password", tags=["Auth"])
async def forgot_password(email: _schemas.CheckEmailReq, db: _orm.Session = Depends(get_db)):
    if not _helpers.validate_email(email.email):
        raise HTTPException(status_code=400, detail="Incorrect email format")
    
    if not await _services.get_user_by_email(email.email,db):
        raise HTTPException(status_code=404, detail="Email not found")
    
    otp = _helpers.generate_otp()
    subject = "Password reset OTP"
    html_body = f"Your password reset OTP is: {otp}\nIf you did not request this, ignore."

    email_sent = _helpers.send_email(email.email, subject, html_body)
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send email")
    _services.save_otp(db, email.email, otp, purpose="reset")

    return JSONResponse(content={"message": f"An OTP has been sent to {email.email}. If you did not receive the email, please check your spam/junk mail folder."}, status_code=200)

@router.post("/auth/reset-password", tags=["Auth"])
async def reset_password(reset_request: _schemas.ResetPasswordReq, db: _orm.Session = Depends(get_db)):
    if not _helpers.validate_email(reset_request.email):
        raise HTTPException(status_code=400, detail="Incorrect email format")
    
    _services.reset_password_using_otp(db, reset_request.email, reset_request.otp, reset_request.new_password)
    return {"message": "Password reset successful"}

@router.post("/refresh_token", tags=["Auth"])
async def refresh_token(token_body:_schemas.verify_token):
 
    print("This is my refresh token:", token_body.token)
    return _helpers.refresh_jwt(token_body.token)


@router.post("/login", response_model=_schemas.AuthLoginResp, tags=["Auth"])
def login(payload: _schemas.LoginReq, db: _orm.Session = Depends(get_db)):
    if payload.email in lockout_expiry:
        if datetime.datetime.utcnow() < lockout_expiry[payload.email]:
            raise HTTPException(status_code=403, detail="Account locked due to multiple failed login attempts. Please try again later.")
        else:
            del lockout_expiry[payload.email]
            login_attempts[payload.email] = 0
    user, access, refresh= _services.login_with_email(db, payload.email, payload.password)
    return {"message": "Login successful", "access_token": access, "user": user, "refresh_token": refresh}

@router.post("/google-login", response_model=_schemas.AuthLoginResp)
def google_login(payload: _schemas.GoogleLoginReq, db: _orm.Session = Depends(get_db)):
    user, access, refresh = _services.login_with_google(db, payload.id_token)
    return {"message": "Login successful", "access_token": access, "refresh_token": refresh, "user": user}



@router.post("/register", response_model=_schemas.AuthLoginResp)
def register(payload: _schemas.RegisterReq, db: _orm.Session = Depends(get_db)):
    password = payload.password if payload.auth_provider == "local" else None
    user, access, refresh = _services.register_user(db, payload, password_plain=password)
    return {"message": "User registered successfully", "access_token": access, "refresh_token": refresh, "user": user}

@router.post("/refresh", response_model=_schemas.MessageResp, tags=["Auth"])
def refresh(payload: _schemas.RefreshReq, db: _orm.Session = Depends(get_db)):
    try:
        new_access = _services.refresh_access_token(db, payload.refresh_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    return {"message": new_access}

@router.post("/check-username", response_model=_schemas.UsernameAvailResp)
def check_username(payload: _schemas.CheckUsernameReq, db: _orm.Session = Depends(get_db)):
    avail = _services.check_username_available(db, payload.username)
    return {"available": avail}


@router.get("/countries", response_model=List[_schemas.CountryRead])
async def read_countries(db: _orm.Session = Depends(get_db)):
    countries = _services.get_all_countries(db=db)
    if not countries:
        raise HTTPException(status_code=404, detail="No countries found")
    return countries


@router.get("/sources", response_model=List[_schemas.SourceRead])
async def read_sources(db: _orm.Session = Depends(get_db)):
    sources = _services.get_all_sources(db=db)
    if not sources:
        raise HTTPException(status_code=404, detail="No sources found")
    return sources
