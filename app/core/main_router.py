import datetime
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError
from app.Client.schema import ClientCreateApp, ClientLogin, ClientLoginResponse, CreateClientCoach, CreateClientMembership, CreateClientOrganization, RegisterClientApp
from app.Coach.schema import CoachAppBase, CoachLogin, CoachLoginResponse, CoachRead,CoachLoginResponse
from app.Coach.service import create_appcoach
import app.Client.service as _client_service 
import app.Coach.service as _coach_service 
import app.Shared.helpers as _helpers
import sqlalchemy.orm as _orm

from app.Shared.schema import UserBase
from ..Shared.dependencies import get_db
import app.user.schema as _schemas
import app.user.models as _models
import app.user.service as _services
import app.core.db.session as _database

import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

router = APIRouter()
login_attempts: Dict[str, int] = {}
lockout_expiry: Dict[str, datetime.datetime] = {}
MAX_ATTEMPTS = 3
LOCKOUT_TIME = datetime.timedelta(minutes=30)


@router.get("/healthcheck", status_code=200)
def healthcheck():
    return JSONResponse(content=jsonable_encoder({"status": "Healthy yayy!"}))

@router.post("/refresh_token", tags=["Auth"])
async def refresh_token(refresh_token: str = Header(None, alias="refresh_token")):
    return _helpers.refresh_jwt(refresh_token)

@router.post("/register/admin")
async def register_user(user: _schemas.UserCreate, db: _orm.Session = Depends(get_db)):
    print("Here 1", user.email, user.password, user.first_name)
    db_user = await _services.get_user_by_email(user.email, db)
    print(f"User: {db_user}")
    print("Here 2")
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    organization_details = _schemas.OrganizationCreateTest(name=user.org_name)
    organization = await _services.create_organizationtest(organization_details, db)

    user_data = user.dict()
    user_data['org_id'] = organization.id
    user_data.pop('org_name')

    user_register = _schemas.UserRegister(**user_data, created_at=datetime.datetime.utcnow())
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
            lockout_expiry[user.email] = datetime.datetime.now() + LOCKOUT_TIME
            raise HTTPException(status_code=403, detail="Account locked. Try again later.")

        raise HTTPException(status_code=401, detail="Invalid email or password")

    login_attempts[user.email] = 0
    user_obj = UserBase.model_validate(authenticated_user)
    user_obj = user_obj.model_dump()
    token = _helpers.create_token(user_obj, "Staff")
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

@router.post(
    "/app/member/signup", response_model=ClientLoginResponse, tags=["App Router"]
)
async def register_mobileclient(
    client: ClientCreateApp, db: _orm.Session = Depends(get_db)
):
    try:
        db_client = await _client_service.get_client_by_email(client.email, db)
        if db_client:
            if db_client.is_deleted:
                updated_client = await _client_service.update_client(
                    db_client.id, client, db
                )
                member_base = dict(id=updated_client.id)
                token = _helpers.create_token(member_base, "Member")
                return {
                    "is_registered": True,
                    "client": updated_client,
                    "access_token": token,
                }
            else:
                raise HTTPException(status_code=400, detail="Email already registered")

        client_data = client.dict()
        organization_id = client_data.pop("org_id", 0)
        status = client_data.pop("status", "pending")
        coach_id = client_data.pop("coach_id", None)
        membership_id = client_data.pop("membership_plan_id", 0)

        client_data["own_member_id"] = _client_service.generate_own_member_id()

        new_client = await _client_service.create_client_for_app(
            RegisterClientApp(**client_data), db
        )

        await _client_service.create_client_organization(
            CreateClientOrganization(
                client_id=new_client.id, org_id=organization_id, client_status=status
            ),
            db,
        )

        await _client_service.create_client_membership(
            CreateClientMembership(
                client_id=new_client.id, membership_plan_id=membership_id
            ),
            db,
        )

        if coach_id is not None:
            await _client_service.create_client_coach(new_client.id, [coach_id], db)
        member_base = dict(id=new_client.id)
        token = _helpers.create_token(member_base, "Member")

        return {"is_registered": True, "client": new_client, "access_token": token}

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(
            status_code=400, detail="Duplicate entry or integrity constraint violation"
        )

    except DataError as e:
        db.rollback()
        logger.error(f"DataError: {e}")
        raise HTTPException(
            status_code=400, detail="Data error occurred, check your input"
        )

   

@router.post("/app/member/login", response_model=ClientLoginResponse,  tags=["App Router"])
async def login_client(client_data: ClientLogin, db: _orm.Session = Depends(get_db)):
    try:
      result = await _client_service.login_client(client_data.email_address, client_data.wallet_address, db)
      print("result",result)
      return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.post("/app/coach/signup", response_model=CoachLoginResponse,tags=["App Router"])
async def create_mobilecoach(coach: CoachAppBase, db: _orm.Session = Depends(get_db)):
    try:
        db_coach =  await _coach_service.get_coach_by_email(coach.email, db)
        print("MY COACH",db_coach)
        if db_coach:
            if db_coach.is_deleted:
                updated_coach = await _coach_service.update_coach(db_coach.id,coach,"app", db)
                coach_base=dict(id=db_coach.id)
                token = _helpers.create_token(coach_base, "Coach")
                return {
                    "is_registered": True,
                    "coach": updated_coach,
                    "access_token": token
                }
            else:
                raise HTTPException(status_code=400, detail="Email already registered")

        new_coach=_coach_service.create_appcoach(coach,db)
        new_coach.org_id=0
        member_base=dict(id=new_coach.id)
        token = _helpers.create_token(member_base, "Coach")
        return {
            "is_registered": True,
            "coach": new_coach,
            "access_token": token
        }

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Duplicate entry or integrity constraint violation")
        
    except DataError as e:
        db.rollback()
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")    
                    


@router.post("/app/coach/login", response_model=CoachLoginResponse,  tags=["App Router"])
async def login_coach(coach_data: CoachLogin, db: _orm.Session = Depends(get_db)):
    try:
        result = await _coach_service.login_coach(coach_data.email_address, coach_data.wallet_address, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
