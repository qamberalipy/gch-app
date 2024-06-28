from typing import Dict, List
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, DataError
import app.user.schema as _schemas
import sqlalchemy.orm as _orm
import app.user.models as _models
import app.user.service as _services
import app.core.db.session as _database
import pika
import logging
import datetime
from datetime import datetime as _dt
import fastapi.security as _security
import app.Shared.helpers as _helpers

router = APIRouter()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

login_attempts: Dict[str, int] = {}
lockout_expiry: Dict[str, datetime.datetime] = {}
MAX_ATTEMPTS = 3
LOCKOUT_TIME = datetime.timedelta(minutes=30)

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
    
    if user.email in lockout_expiry and datetime.datetime.now() < lockout_expiry[user.email]:
        raise HTTPException(status_code=403, detail="Account locked. Try again later.")

    authenticated_user = await _services.authenticate_user(user.email, user.password, db)
    if not authenticated_user:
        login_attempts[user.email] = login_attempts.get(user.email, 0) + 1

        if login_attempts[user.email] >= MAX_ATTEMPTS:
            # Lock the account if maximum attempts are reached
            lockout_expiry[user.email] = datetime.now() + LOCKOUT_TIME
            raise HTTPException(status_code=403, detail="Account locked. Try again later.")

        raise HTTPException(status_code=401, detail="Invalid email or password")

    login_attempts[user.email] = 0
    # token = await _services.create_token(authenticated_user)
    token = _helpers.create_token(authenticated_user, "User")
    user_data = await _services.get_alluser_data(email=user.email, db=db)
    return {
        "user": user_data,
        "token": token
    }


@router.post("/test_token")
async def test_token(
        token: str,
        db: _orm.Session = Depends(get_db)
    ):
    print("Token 1: ", token)
    payload = _helpers.verify_jwt(token, "User")
    return payload

    
@router.get("/get_all_countries/", response_model=List[_schemas.CountryRead])
async def read_countries(db: _orm.Session = Depends(get_db)):
    countries = _services.get_all_countries(db=db)
    if not countries:
        raise HTTPException(status_code=404, detail="No countries found")
    return countries

@router.get("/get_all_sources/", response_model=List[_schemas.SourceRead])
async def read_sources(db: _orm.Session = Depends(get_db)):
    sources = _services.get_all_sources(db=db)
    if not sources:
        raise HTTPException(status_code=404, detail="No sources found")
    return sources

@router.post("/get_staff",response_model=List[_schemas.getStaff])
async def get_staff(user: _schemas.getStaff, db: _orm.Session= Depends(get_db)):
    filtered_users=  db.query(_models.User).filter(_models.User.org_id == user.org_id).all()
    response_users = [map_lead_to_response(lead) for lead in filtered_users]
    return response_users

def map_lead_to_response(user) -> _schemas.getStaff:
   return _schemas.getStaff(
        name=user.username,
        id=user.id,
        org_id=user.org_id)
    