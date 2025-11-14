# app/user/main_router.py
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import app.Shared.helpers as _helpers
from app.Shared import schema as _schemas
from app.user import service as _services

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/api")

# simple rate-limited lockout (memory-based) for failed login attempts
login_attempts = {}
LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION_SECONDS = 30 * 60  # 30 minutes


@router.get("/healthcheck", status_code=200)
def healthcheck():
    return {"status": "healthy"}


@router.post("/auth/check-email", response_model=_schemas.ExistsResp, tags=["Auth"])
def check_email(payload: _schemas.CheckEmailReq, db: Session = Depends(_services.get_db)):
    if not _helpers.validate_email(payload.email):
        raise HTTPException(status_code=400, detail="Incorrect email format")
    exists = _services.check_email_exists(db, payload.email)
    return {"exists": exists}


@router.post("/auth/send-otp", tags=["Auth"])
def send_otp(payload: _schemas.SendOtpReq, db: Session = Depends(_services.get_db)):
    if not _helpers.validate_email(payload.email):
        raise HTTPException(status_code=400, detail="Incorrect email format")

    otp = _helpers.create_otp()
    subject = "OTP from your application"
    html_body = f"<p>Your OTP: <strong>{otp}</strong></p><p>If you did not request this, ignore.</p>"

    sent = _helpers.send_email(payload.email, subject, html_body)
    print(sent)
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send email")

    _services.save_otp(db, payload.email, otp, purpose="verify")
    return JSONResponse(content={"message": "OTP sent"}, status_code=200)


@router.post("/auth/verify-otp", tags=["Auth"])
def verify_otp(payload: _schemas.VerifyOtpReq, db: Session = Depends(_services.get_db)):
    if not _helpers.validate_email(payload.email):
        raise HTTPException(status_code=400, detail="Incorrect email format")
    ok = _services.verify_otp(db, payload.email, payload.otp, purpose="verify")
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    return {"message": "OTP verified successfully"}


@router.post("/auth/forgot-password", tags=["Auth"])
def forgot_password(payload: _schemas.ForgotPasswordReq, db: Session = Depends(_services.get_db)):
    if not _helpers.validate_email(payload.email):
        raise HTTPException(status_code=400, detail="Incorrect email format")
    if not _services.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=404, detail="Email not found")
    otp = _helpers.create_otp()
    subject = "Password reset OTP"
    html_body = f"<p>Your password reset OTP: <strong>{otp}</strong></p>"
    if not _helpers.send_email(payload.email, subject, html_body):
        raise HTTPException(status_code=500, detail="Failed to send email")
    _services.save_otp(db, payload.email, otp, purpose="reset")
    return {"message": "OTP sent for password reset"}


@router.post("/auth/reset-password", tags=["Auth"])
def reset_password(payload: _schemas.ResetPasswordReq, db: Session = Depends(_services.get_db)):
    if not _helpers.validate_email(payload.email):
        raise HTTPException(status_code=400, detail="Incorrect email format")
    _services.reset_password_using_otp(db, payload.email, payload.otp, payload.new_password)
    return {"message": "Password reset successful"}


@router.post("/auth/register", response_model=_schemas.AuthLoginResp, tags=["Auth"])
def register(payload: _schemas.RegisterReq, db: Session = Depends(_services.get_db)):
    user, access_token, refresh_token = _services.register_user(db, payload)
    return {"message": "User registered", "access_token": access_token, "refresh_token": refresh_token, "user": user}


@router.post("/auth/login", response_model=_schemas.AuthLoginResp, tags=["Auth"])
def login(payload: _schemas.LoginReq, db: Session = Depends(_services.get_db)):
    # lockout check
    attempts = login_attempts.get(payload.email, {"count": 0, "locked_until": None})
    if attempts.get("locked_until") and attempts["locked_until"] > datetime.utcnow():
        raise HTTPException(status_code=403, detail="Account locked due to multiple failed attempts")

    try:
        user, access_token, refresh_token = _services.login_with_email(db, payload.email, payload.password)
        # reset attempts on success
        login_attempts.pop(payload.email, None)
        return {"message": "Login successful", "access_token": access_token, "refresh_token": refresh_token, "user": user}
    except HTTPException as e:
        # increment attempts
        attempts = login_attempts.setdefault(payload.email, {"count": 0, "locked_until": None})
        attempts["count"] += 1
        if attempts["count"] >= LOCKOUT_THRESHOLD:
            attempts["locked_until"] = datetime.utcnow() + timedelta(seconds=LOCKOUT_DURATION_SECONDS)
        raise e


@router.post("/auth/google", response_model=_schemas.AuthLoginResp, tags=["Auth"])
def google_login(payload: _schemas.GoogleLoginReq, db: Session = Depends(_services.get_db)):
    user, access_token, refresh_token = _services.login_with_google(db, payload.id_token)
    return {"message": "Login successful", "access_token": access_token, "refresh_token": refresh_token, "user": user}


@router.post("/auth/refresh", tags=["Auth"])
def refresh(payload: _schemas.RefreshReq, db: Session = Depends(_services.get_db)):
    try:
        new_access = _services.refresh_access_token(db, payload.refresh_token)
        return {"message": new_access}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/logout", tags=["Auth"])
def logout(payload: Optional[_schemas.RefreshReq], db: Session = Depends(_services.get_db)):
    token = payload.refresh_token if payload else None
    _services.logout_user(db, refresh_token=token)
    return {"message": "Logged out"}
        

@router.get("/countries", response_model=List[_schemas.UserOut], tags=["Misc"])
def read_countries(db: Session = Depends(_services.get_db)):
    countries = _services.get_all_countries(db)
    if not countries:
        raise HTTPException(status_code=404, detail="No countries found")
    # return country list as dictionaries if you prefer; here we will just return raw ORM list (pydantic not configured for Country)
    return countries


@router.get("/sources", tags=["Misc"])
def read_sources(db: Session = Depends(_services.get_db)):
    sources = _services.get_all_sources(db)
    if not sources:
        raise HTTPException(status_code=404, detail="No sources found")
    return sources
