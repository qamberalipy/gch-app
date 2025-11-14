# app/Shared/helpers.py
import os
import time
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any
import re
from passlib.context import CryptContext
import fastapi as _fastapi
import requests  # for Brevo API

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET")
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "900"))  # 15 minutes default
REFRESH_TOKEN_EXPIRE_SECONDS = int(os.getenv("REFRESH_TOKEN_EXPIRE_SECONDS", str(60 * 60 * 24 * 7)))  # 7 days

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "qamber.qsol@gmail.com")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "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")

EMAIL_REGEX = re.compile(r"^(?=.{1,254}$)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

# ----------------- Utility Functions -----------------
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
            "sub": str(user_id),
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
            "sub": str(user_id),
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
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise _fastapi.HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise _fastapi.HTTPException(status_code=401, detail="Invalid token")

def create_otp(length: int = 6) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length))

# ----------------- Brevo Email -----------------
def send_email(recipient_email: str, subject: str, html_text: str, otp: str) -> bool:

    html_body= generate_otp_email_html(otp, html_text)
    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    payload = {
        "sender": {"name": "Qamber Ali", "email": SENDER_EMAIL},
        "to": [{"email": recipient_email}],
        "subject": subject,
        "htmlContent": html_body
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201, 202]:
            print("Email sent successfully via Brevo!")
            return True
        else:
            print("Brevo API error:", response.status_code, response.text)
            return False
    except Exception as e:
        print("Error sending email via Brevo:", e)
        return False

def generate_otp_email_html(otp: str, message: str = None) -> str:
    """
    Generate a modern OTP email HTML body.
    
    :param otp: OTP string to show in email.
    :param message: Custom message for the email body. If None, default message will be used.
    :return: HTML string.
    """
    if message is None:
        message = (
            "Thank you for choosing <strong>Link Nest</strong>. "
            "Use the following OTP to complete your sign-up procedure. "
            "This OTP is valid for <strong>5 minutes</strong>."
        )
    
    html_body = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; min-width: 1000px; overflow: auto; line-height: 1.6; background-color: #f9f9f9; padding: 40px 0;">
      <div style="margin: 0 auto; width: 600px; background-color: #ffffff; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); overflow: hidden;">
        
        <!-- Header -->
        <div style="background-color: #1a73e8; padding: 20px; text-align: center;">
          <a href="#" style="font-size: 1.6em; color: #ffffff; text-decoration: none; font-weight: 700;">Link Nest</a>
        </div>
        
        <!-- Body -->
        <div style="padding: 30px 40px; text-align: center;">
          
          <p style="font-size: 1em; color: #555555; margin-bottom: 30px;">
            {message}
          </p>
          
          <!-- OTP -->
          <div style="display: inline-block; background-color: #1a73e8; color: #ffffff; font-size: 1.5em; font-weight: 700; padding: 15px 25px; border-radius: 8px; letter-spacing: 3px;">
            {otp}
          </div>
          
          <p style="font-size: 0.9em; color: #777777; margin-top: 30px;">
            Regards,<br>
            <strong>Link Nest Team</strong>
          </p>
        </div>
        
      </div>
    </div>
    """
    return html_body
