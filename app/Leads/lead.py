import json
from typing import List, Optional
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.exc import IntegrityError, DataError
import app.Leads.schema as _schemas
import sqlalchemy.orm as _orm
import app.Leads.models as _models
import app.Leads.service as _services
import app.user.service as _user_service
import app.core.db.session as _database
import pika
import fastapi as _fastapi
import logging
import datetime
import app.Shared.helpers as _helpers

router = APIRouter(tags=["Lead Router"])

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
    

@router.post("/leads",response_model= _schemas.LeadCreate)
async def register_lead(lead_data: _schemas.LeadCreate, db: _orm.Session = Depends(get_db)):
    try:
        
        
        
        existing_lead = await _services.get_lead_by_email(lead_data.email, db)
        if existing_lead:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email address is already registered. Please use a different email address or log in if you already have an account."
            )

        # Create new lead if email does not exist
        new_lead = await _services.create_lead(_schemas.LeadCreate(**lead_data.model_dump()), db)
        return new_lead

    except DataError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

    

@router.get("/leads", response_model=List[_schemas.ResponseLeadRead])
async def get_leads(
    org_id: int, 
    request: Request,
    limit: Optional[int]=None, 
    offset: Optional[int]=None,  
    db: _orm.Session = Depends(get_db)):
    try:
        
        
        
        params = {
            "org_id": org_id,
            "limit": limit,
            "offset": offset,
            "first_name": request.query_params.get("first_name", None),
            "mobile": request.query_params.get("mobile", None),
            "owner": request.query_params.get("owner", None),
            "status": request.query_params.get("status", None),
            "source": request.query_params.get("source", None),
            "search": request.query_params.get("search", None)
        }

        filtered_leads = await _services.get_leads(db, params=_schemas.LeadRead(**params))
        return filtered_leads
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.put('/leads/staff', response_model=_schemas.UpdateStaff)
async def update_status(data: _schemas.UpdateStaff, db: _orm.Session = Depends(get_db)):
    try:    
        
        db_lead = await _services.update_staff(data,db)    
        return db_lead
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.put('/leads/status', response_model=_schemas.UpdateStatus)
async def update_status(data: _schemas.UpdateStatus, db: _orm.Session = Depends(get_db)):
    try:
        
        db_lead = await _services.update_status(data,db)    
        return db_lead
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.put('/leads', response_model=_schemas.LeadUpdate)
async def update_data(lead_id:int,data: _schemas.LeadUpdate, db: _orm.Session = Depends(get_db)):
    try:
        
        db_lead = await _services.update_data(lead_id,data,db)    
        return db_lead
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.get("/leads")
async def get_lead_by_id(lead_id:int,db: _orm.Session = Depends(get_db)):
    try:
        
        
        existing_lead = await _services.get_lead_by_id(lead_id, db)
        return existing_lead
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")