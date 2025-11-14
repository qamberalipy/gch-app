# app/Shared/helpers.py
import os
import time
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from passlib.context import CryptContext
import fastapi as _fastapi

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET")
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "900"))  # 15 minutes default
REFRESH_TOKEN_EXPIRE_SECONDS = int(os.getenv("REFRESH_TOKEN_EXPIRE_SECONDS", str(60 * 60 * 24 * 7)))  # 7 days

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "qamber.qsol@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD","jymavqwsguhvivnv")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

EMAIL_REGEX = re.compile(r"^(?=.{1,254}$)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email))


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_ctx.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(user_id: int) -> str:
    try:
        now = datetime.utcnow()
        payload = {
            "sub": str(user_id),           # always use string
            "type": "access",
            "iat": now,
            "exp": now + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        return token
    except Exception:
        raise _fastapi.HTTPException(status_code=500, detail="Failed to create access token")


def create_refresh_token(user_id: int) -> str:
    try:
        now = datetime.utcnow()
        payload = {
            "sub": str(user_id),          # always use string
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(seconds=REFRESH_TOKEN_EXPIRE_SECONDS)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        return token
    except Exception:
        raise _fastapi.HTTPException(status_code=500, detail="Failed to create refresh token")


def decode_token(token: str) -> Dict[str, Any]:
    try:
        print("JWT_SECRET",JWT_SECRET)
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise _fastapi.HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise _fastapi.HTTPException(status_code=401, detail="Invalid token")

def create_otp(length: int = 6) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length))


def send_email(recipient_email: str, subject: str, html_body: str) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email
    print("data",SENDER_EMAIL,SENDER_PASSWORD,SMTP_SERVER,SMTP_PORT)
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False
