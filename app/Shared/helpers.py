from datetime import date, datetime
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
        
        payload["token_time"] = time.time()
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        return dict(access_token=token, token_type="bearer")
    
    except jwt.ExpiredSignatureError:
        raise _fastapi.HTTPException(status_code=400, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise _fastapi.HTTPException(status_code=400, detail="Invalid refresh token")
    
def generate_password_reset_token(user_data_json):
    
    serial = Serializer('LetsMove')
    # token = serial.dumps({'user_id': f'{user_id}'})
    token = serial.dumps(user_data_json)
    print('Token:', token)
    return token

def verify_password_reset_token(token: str):
    
    serial = Serializer('LetsMove')
    try:
        data = serial.loads(token, max_age=1800)
        return data
    except SignatureExpired:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception as e:
        logging.error(f"Error verifying password reset token: {e}")
        raise _fastapi.HTTPException(status_code=500, detail="Internal Server Error")