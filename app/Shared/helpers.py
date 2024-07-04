from datetime import date
import jwt, json, time, os, random, logging, bcrypt as _bcrypt
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.user.schema as _u_schemas
import app.Coach.schema as _co_schemas
import app.user.models as _models


user_type_mapping = {
    "User": _u_schemas.UserBase,
    "Coach": _co_schemas.CoachBase
}
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRY = os.getenv("JWT_EXPIRY")

def create_token(obj, obj_type: str):
    schema_class = user_type_mapping.get(obj_type)
    print("In Create Token")
    if schema_class is None:
        raise ValueError("Invalid user type")

    user_obj = schema_class.from_orm(obj)
    user_dict = user_obj.dict()
    print(user_dict)
    if "date_created" in user_dict:
        del user_dict["date_created"]
    user_dict['token_time'] = time.time()
    user_dict['user_type'] = obj_type.lower()
    token = jwt.encode(user_dict, JWT_SECRET, algorithm="HS256")
    return dict(access_token=token, token_type="bearer")


def verify_jwt(token: str, obj_type: str = "User"):
    # Verify a JWT token
    credentials_exception = _fastapi.HTTPException(
        status_code=_fastapi.status.HTTP_401_UNAUTHORIZED,
        detail = "Token Expired or Invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print(JWT_EXPIRY)
        token = token.split("Bearer ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print("Payload",payload)
        print("Time Difference", time.time() - payload["token_time"])
       
        if (time.time() - payload["token_time"]) > int(JWT_EXPIRY):
            print("Token Expired")
            raise credentials_exception
        if payload['user_type'] != obj_type.lower():
            raise credentials_exception

        return payload
    except:
        raise credentials_exception

def get_current_user(request: _fastapi.Request):
    authorization: str = request.headers.get("Authorization")
    if not authorization:
        raise _fastapi.HTTPException(status_code=_fastapi.status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization
    return verify_jwt(token)        