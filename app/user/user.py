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

@router.post("/register/client", response_model=_schemas.ClientRead)
async def register_client(client: _schemas.ClientCreate, db: _orm.Session = Depends(get_db)):    
    
    try:
        db_client = await _services.get_user_by_email(client.email_address, db)
        if db_client:
            raise HTTPException(status_code=400, detail="Email already registered")

        client_data = client.dict()
        organization_id = client_data.get('org_id')
        coach_id=client_data.get('coach_id')
        membership_id=client_data.get('membership_id')
        client_data.pop('org_id')
        client_data.pop('coach_id')
        client_data.pop('membership_id')

        new_client = await _services.create_client(_schemas.RegisterClient(**client_data), db)
        # client_organization_detail = _schemas.CreateClient_Organization(
        #     client_id=new_client.id,
        #     org_id=organization_id
        # )

        
        await _services.create_client_organization(_schemas.CreateClient_Organization(client_id=new_client.id,org_id=organization_id), db)
        await _services.create_client_membership(_schemas.CreateClient_membership(client_id=new_client.id,membership_plan_id=membership_id), db)
        await _services.create_client_coach(_schemas.CreateClient_coach(client_id=new_client.id,coach_id=coach_id), db)
        
        return new_client

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate entry or integrity constraint violation")

    except DataError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# @router.post("/register/client", response_model=_schemas.ClientRead)
# async def register_client(client: _schemas.ClientCreate,  db: _orm.Session = Depends(get_db)):
#     try:
#         db_client = await _services.get_user_by_email(client.email_address, db)
#         if db_client:
#             raise HTTPException(status_code=400, detail="Email already registered")
        
#         new_client = await _services.create_client(client, db)
#         return new_client
        
#     except IntegrityError:
#         db.rollback()
#         raise HTTPException(status_code=400, detail="Duplicate entry or integrity constraint violation")
    
#     except DataError:
#         db.rollback()
#         raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


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


@router.post("/login/client", response_model=dict)
async def login_client(client_login: _schemas.ClientLogin, db: _orm.Session = Depends(get_db)):
    logger.debug("Here 1", client_login.email_address, client_login.wallet_address)
    
    authenticated_client = await _services.authenticate_client(client_login.email_address, client_login.wallet_address, db)
    
    if not authenticated_client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    token = await _services.create_token(authenticated_client)
    return token

@router.get("/clients/{client_id}", response_model=_schemas.ClientRead)
async def get_client(client_id: int, db: _orm.Session = Depends(get_db)):
    client = await _services.get_client_by_id(client_id, db)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


# API FOR COACHES

@router.post("/coaches/", response_model=_schemas.CoachRead)
async def register_coach(coach: _schemas.CoachCreate, db: _orm.Session = Depends(get_db)):
    return _services.create_coach(db=db, coach=coach)

@router.get("/coaches/{org_id}", response_model=List[_schemas.CoachRead])
async def read_coaches(org_id: int, db: _orm.Session = Depends(get_db)):
    coaches = _services.get_coaches_by_org_id(db=db, org_id=org_id)
    if not coaches:
        raise HTTPException(status_code=404, detail="No coaches found for this organization")
    return coaches