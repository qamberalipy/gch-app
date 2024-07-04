from typing import List, Optional
from fastapi import Header,FastAPI, APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError, DataError
import app.Client.schema as _schemas
import sqlalchemy.orm as _orm
import app.Client.models as _models
import app.Client.service as _services
import app.user.service as _user_service
import app.Shared.helpers as _helpers
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
        
@router.post("/register", response_model=_schemas.ClientRead, tags=["Client Router"])
async def register_client(client: _schemas.ClientCreate, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        
        db_client = await _services.get_client_by_email(client.email, db)
        if db_client:
            raise HTTPException(status_code=400, detail="Email already registered")

        client_data = client.dict()
        organization_id = client_data.pop('org_id')
        status = client_data.pop('status')
        coach_id = client_data.pop('coach_id', None)
        membership_id = client_data.pop('membership_id')

        new_client = await _services.create_client(_schemas.RegisterClient(**client_data), db)
        
        await _services.create_client_organization(
            _schemas.CreateClientOrganization(client_id=new_client.id, org_id=organization_id, client_status=status), db
        )

        await _services.create_client_membership(
            _schemas.CreateClientMembership(client_id=new_client.id, membership_plan_id=membership_id), db
        )

        if coach_id is not None:
            await _services.create_client_coach(
                _schemas.CreateClientCoach(client_id=new_client.id, coach_id=coach_id), db
            )

        return new_client

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Duplicate entry or integrity constraint violation")
        
    except DataError as e:
        db.rollback()
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

    


@router.post("/mobile/register", response_model=_schemas.ClientLoginResponse, tags=["App Router"])
async def register_mobileclient(client: _schemas.ClientCreateApp, db: _orm.Session = Depends(get_db)):
    try:
        db_client = await _services.get_client_by_email(client.email, db)
        if db_client:
            raise HTTPException(status_code=400, detail="Email already registered")

        client_data = client.dict()
        organization_id = client_data.pop('org_id', 0)
        status = client_data.pop('status', 'pending')
        coach_id = client_data.pop('coach_id', None)
        membership_id = client_data.pop('membership_id', 0)

        # Generate random own_member_id
        client_data['own_member_id'] = _services.generate_own_member_id()

        new_client = await _services.create_client_for_app(_schemas.RegisterClientApp(**client_data), db)

        await _services.create_client_organization(
            _schemas.CreateClientOrganization(client_id=new_client.id, org_id=organization_id, client_status=status), db
        )

        await _services.create_client_membership(
            _schemas.CreateClientMembership(client_id=new_client.id, membership_plan_id=membership_id), db
        )

        if coach_id is not None:
            await _services.create_client_coach(
                _schemas.CreateClientCoach(client_id=new_client.id, coach_id=coach_id), db
            )
        token = _helpers.create_token(new_client, "User")
        return {
            "is_registered":True,
            "client":new_client,
            "access_token":token
        }

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Duplicate entry or integrity constraint violation")
        
    except DataError as e:
        db.rollback()
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

    
 
    
    
@router.put("/update/{client_id}", response_model=_schemas.ClientRead, tags=["Client Router"])
async def update_client(client_id: int, client: _schemas.ClientUpdate, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        
        # Update client details
        updated_client = await _services.update_client(client_id, client, db)
        
        if client.membership_id is not None:
            await _services.update_client_membership(client_id, client.membership_id, db)

        if client.coach_id is not None:
            await _services.update_client_coach(client_id, client.coach_id, db)
        
        return updated_client

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Duplicate entry or integrity constraint violation")

    except DataError as e:
        db.rollback()
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

    

@router.delete("/delete/{client_id}", response_model=_schemas.ClientRead, tags=["Client Router"])
async def delete_client(client_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        
        deleted_client = await _services.delete_client(client_id, db)
        return deleted_client

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity constraint violation")

    except DataError as e:
        db.rollback()
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

    


@router.post("/login", response_model=_schemas.ClientLoginResponse,  tags=["App Router"])
async def login_client(client_data: _schemas.ClientLogin, db: _orm.Session = Depends(get_db)):
    try:
        print(client_data)
        result = await _services.login_client(client_data.email_address, client_data.wallet_address, db)
        print(result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/{client_id}", response_model=_schemas.ClientByID, tags=["Client Router"])
async def get_client_by_id(client_id: int, db:  _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:    
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        client = await _services.get_client_byid(db=db, client_id=client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return client    
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    
@router.get("/filter/", response_model=List[_schemas.ClientFilterRead], tags=["Client Router"])
async def get_client(
    org_id: int,
    request: Request,
    db: _orm.Session = Depends(get_db),
    authorization: str = Header(None)):
    try:    
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        print("MY LIST ",Request)
        params = {
            "org_id": org_id,
            "search_key": request.query_params.get("search_key"),
            "client_name": request.query_params.get("client_name"),
            "status": request.query_params.get("status"),
            "coach_assigned": request.query_params.get("coach_assigned"),
            "membership_plan": request.query_params.get("membership_plan"),
            "limit":request.query_params.get('limit') ,
            "offset":request.query_params.get('offset')
        }
        clients = _services.get_filtered_clients(db=db, params=_schemas.ClientFilterParams(**params))
        return clients
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    

@router.get("/business/{org_id}", response_model=List[_schemas.ClientBusinessRead], tags=["Client Router"])
async def get_business_clients(org_id: int,db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        clients = await _services.get_business_clients(org_id, db)
        if not clients:
            return []
        return clients
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
@router.get("/getTotalClient/{org_id}", response_model=_schemas.ClientCount, tags=["Client Router"])
async def get_total_clients(org_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        
        total_clients = await _services.get_total_clients(org_id, db)
        return {"total_clients": total_clients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
