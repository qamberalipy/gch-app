from typing import Annotated, List, Optional
from fastapi import Header,FastAPI, APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError, DataError
import app.Client.schema as _schemas
import sqlalchemy.orm as _orm
import app.Client.models as _models
import app.Client.service as _services
import app.Client.schema as _schemas
from app.Shared.dependencies import get_user
import app.user.service as _user_service
import app.Shared.helpers as _helpers
# from main import logger
import app.core.db.session as _database
import pika
import logging
import datetime
from app.Client.models import ClientStatus
from app.Shared.schema import SharedCreateSchema,SharedModifySchema

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
        
@router.post("/member",response_model=SharedCreateSchema, tags=["Member Router"])
async def register_client(client: _schemas.ClientCreate,request:Request,db: _orm.Session = Depends(get_db)):
    try:
        if not _helpers.validate_email(client.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        user_id=request.state.user.get('id')
        db_client = await _services.get_client_by_email(client.email, db)
        if db_client:
            raise HTTPException(status_code=400, detail="Email already registered")

        client_data = client.dict()
        organization_id = client_data.pop('org_id')
        status = client_data.pop('client_status')
        coach_ids = client_data.pop('coach_id', [])
        membership_id = client_data.pop('membership_plan_id')
        prolongation_period=client_data.pop('prolongation_period')
        auto_renew_days=client_data.pop('auto_renew_days')
        inv_days_cycle=client_data.pop('inv_days_cycle')
        auto_renewal=client_data.pop('auto_renewal')
        client_data['created_by']=user_id
        client_data['updated_by']=user_id


        new_client = await _services.create_client(_schemas.RegisterClient(**client_data), db)
        
        await _services.create_client_organization(
            _schemas.CreateClientOrganization(client_id=new_client.id, org_id=organization_id, client_status=status), db
        )

        await _services.create_client_membership(
            _schemas.CreateClientMembership(client_id=new_client.id, membership_plan_id=membership_id,auto_renewal=auto_renewal,prolongation_period=prolongation_period,auto_renew_days=auto_renew_days,inv_days_cycle=inv_days_cycle), db
        )

        if coach_ids is not None:
            await _services.create_client_coach(new_client.id, coach_ids, db)

        return {
            "status_code": "201",
            "id": new_client.id,
            "message": "Member created successfully"
        }

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Duplicate entry or integrity constraint violation")
        
    except DataError as e:
        db.rollback()
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


    
@router.put("/member",response_model = _schemas.ClientUpdate, tags=["Member Router"])
async def update_client(client: _schemas.ClientUpdate, db: _orm.Session = Depends(get_db)):
    try:

        
        updated_client = await _services.update_client(client.id, client, db)
        
        if client.membership_plan_id is not None:
            membership = _schemas.ClientMembership(
            client_id=client.id,
            membership_plan_id=client.membership_plan_id,
            auto_renewal=client.auto_renewal,
            prolongation_period=client.prolongation_period,
            auto_renew_days=client.auto_renew_days,
            inv_days_cycle=client.inv_days_cycle
            )
            await _services.update_client_membership(membership, db)

        if client.coach_id:
            await _services.update_client_coach(client.id, client.coach_id, db)
        
        return updated_client

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Duplicate entry or integrity constraint violation")

    except DataError as e:
        db.rollback()
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    

@router.delete("/member/{id}",response_model=SharedModifySchema, tags=["Member Router"])
async def delete_client(id:int, db: _orm.Session = Depends(get_db)):
    try:
        
        deleted_client = await _services.delete_client(id, db)
        return deleted_client

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code = 400, detail="Integrity constraint violation")

    except DataError as e:
        db.rollback()
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code = 400, detail="Data error occurred, check your input")

@router.get("/member/{id}", response_model=_schemas.ClientByID, tags=["Member Router"])
async def get_client_by_id(id: int, db:  _orm.Session = Depends(get_db)):
    try:    
        client = await _services.get_client_byid(db=db, client_id=id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return client    
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


def get_filters(

    search_key: Annotated[str | None, Query(title="Search Key")] = None,
    member_name: Annotated[str, Query(description="Member First/Last Name")] = None,
    status: Annotated[ClientStatus | None, Query(title="status")] = None,
    coach_assigned: Annotated[int, Query(description="Coach ID")] = None,
    membership_plan: Annotated[int, Query(description="Membership ID")] = None,
    sort_order: Annotated[str,Query(title="Sorting Order")] = 'desc',
    sort_key:Annotated[str,Query(title="Sort Key")] =None,
    limit: Annotated[int, Query(description="Pagination Limit")] = None,
    offset: Annotated[int, Query(description="Pagination offset")] = None
):
    return _schemas.ClientFilterParams(
        search_key=search_key,
        member_name=member_name,
        status=status,
        coach_assigned=coach_assigned,
        membership_plan=membership_plan,
        sort_order = sort_order,
        sort_key = sort_key,
        limit=limit,
        offset = offset
    )

@router.get("/member",tags=["Member Router"])
async def get_client( 
    org_id: Annotated[int, Query(title="Organization id")],
    filters: Annotated[_schemas.ClientFilterParams, Depends(get_filters)] = None,
    db: _orm.Session = Depends(get_db)):

    try:
        clients = _services.get_filtered_clients(db=db,org_id=org_id,params=filters)

        if clients:
            return clients
        else:
            raise HTTPException(status_code=404, detail="No clients found")

    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.get("/member/list/{org_id}", response_model=List[_schemas.ClientList], tags=["Member Router"])
async def get_client_list(org_id: int,db: _orm.Session = Depends(get_db)):
    
    try:
        clients = _services.get_list_clients(org_id=org_id, db=db)
        
        if clients:
            return clients
        else:
            raise HTTPException(status_code=404, detail="Client not found")

    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

    

@router.get("/member/business/{org_id}", response_model=List[_schemas.ClientBusinessRead], tags=["Member Router"])
async def get_business_clients(org_id: int,db: _orm.Session = Depends(get_db)):
    try:
        
        clients = await _services.get_business_clients(org_id, db)
        if not clients:
            return []
        return clients
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    

@router.get("/member/count/{org_id}", response_model=_schemas.ClientCount, tags=["Member Router"])
async def get_total_clients(org_id: int, db: _orm.Session = Depends(get_db)):
    try:
        
        total_clients = await _services.get_total_clients(org_id, db)
        return {"total_members": total_clients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
