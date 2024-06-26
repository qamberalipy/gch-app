from typing import List
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, DataError
import app.user.schema as _schemas
import sqlalchemy.orm as _orm
import app.user.models as _models
import app.user.service as _services
# from main import logger
import app.core.db.session as _database
import pika
import logging
import datetime

router = APIRouter()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register/admin")
async def register_user(user: _schemas.UserCreate, db: _orm.Session = Depends(get_db)):
    print("Here 1", user.email, user.password, user.username)
    db_user = await _services.get_user_by_email(user.email, db)
    print(f"User: {db_user}")
    print("Here 2")
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    organization_details = _schemas.OrganizationCreate(org_name=user.org_name)
    organization = await _services.create_organization(organization_details, db)

    user_data = user.dict()
    user_data['org_id'] = organization.id
    user_data.pop('org_name')

    user_register = _schemas.UserRegister(**user_data, date_created=datetime.datetime.utcnow())
    new_user = await _services.create_user(user_register, db)
    
    return new_user

@router.post("/login")
async def login(user: _schemas.GenerateUserToken,db: _orm.Session = Depends(get_db)):
    logger.debug("Here 1", user.email, user.password)
    authenticated_user = await _services.authenticate_user(user.email, user.password, db)
    
    if not authenticated_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    token= await _services.create_token(authenticated_user)
    user_data = await _services.get_alluser_data(email=user.email, db=db)
    return {
        "user": user_data,
        "token": token
    }




