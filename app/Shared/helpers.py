from datetime import date, datetime
import secrets
from typing import Annotated, Any, Dict
from fastapi.exceptions import HTTPException
import jwt, json, time, os, random, logging, bcrypt as _bcrypt
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_ 
import re 
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
from .schema import UserBase, CoachBase
from itsdangerous import URLSafeTimedSerializer as Serializer 
from itsdangerous import SignatureExpired
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_SERVER = os.getenv("SMTP_SERVER")


JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_EXPIRY = os.getenv("JWT_EXPIRY", "")

def create_token(payload: Dict[str, Any], persona: str):
    payload['token_time'] = time.time()
    payload['user_type'] = persona.lower()
    access_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return dict(access_token=access_token,token_type="bearer")

def validate_email(email: str) -> bool:
    # Define the regex pattern for email validation
    pattern = r"^(?=.{1,50}$)[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    
    # Match the email against the pattern
    return bool(re.match(pattern, email))

def verify_jwt(token: str, obj_type: str = "User"):
    # Verify a JWT token
    credentials_exception = _fastapi.HTTPException(
        status_code=_fastapi.status.HTTP_401_UNAUTHORIZED,
        detail = "Token Expired or Invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = token.split("Bearer ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print("Token time: ", (time.time() - payload["token_time"]) > int(JWT_EXPIRY), time.time() - payload["token_time"], int(JWT_EXPIRY))
        if (time.time() - payload["token_time"]) > int(JWT_EXPIRY):
            raise credentials_exception
        if payload['user_type'] != obj_type.lower():
            raise credentials_exception

        return payload
    except:
        raise credentials_exception

def refresh_jwt(refresh_token: str):
    try:
        
        payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=["HS256"])
        # if payload["user_type"] != "user":
        #     raise _fastapi.HTTPException(status_code=400, detail="Invalid user type")
        print("payload", payload)
        payload['token_time'] = time.time()
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        return dict(access_token=token, token_type="bearer")
    
    except jwt.ExpiredSignatureError:
        raise _fastapi.HTTPException(status_code=400, detail='Refresh token expired. ')
    except jwt.InvalidTokenError:
        raise _fastapi.HTTPException(status_code=400, detail='Invalid refresh token. ')
 
def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])   
    
def generate_otp(length: int = 6) -> str:
    # numeric OTP
    return "".join(secrets.choice("0123456789") for _ in range(length))


def send_email(recipient_email: str, subject: str, html_body: str) -> bool:
    sender_email = "qamber.qol@gmail.com"
    sender_password = SENDER_PASSWORD
    smtp_server = SMTP_SERVER
    smtp_port = SMTP_PORT

    # Create a MIME multipart message
    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    # Attach the HTML body
    part = MIMEText(html_body, "html")
    msg.attach(part)

    try:
        # Set up the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)

        # Send the email
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def hash_password(password):
    # Hash a password
    return pwd_ctx.hash(password)
    
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)