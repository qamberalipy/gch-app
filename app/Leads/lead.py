import json
from typing import List, Optional
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError, DataError
import app.Leads.schema as _schemas
import sqlalchemy.orm as _orm
import app.Leads.models as _models
import app.Leads.service as _services
import app.user.service as _user_service
import app.core.db.session as _database
import pika
import logging
import datetime


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
        
    
@router.post("/register/lead", response_model=_schemas.LeadCreate)
async def register_lead(lead_data: _schemas.LeadCreate, db: _orm.Session = Depends(get_db)):   
    try:
        new_lead = await _services.create_lead(_schemas.LeadCreate(**lead_data.model_dump()), db)
        return new_lead

    except DataError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/getleads", response_model=List[_schemas.ResponseLeadRead])
async def get_leads(org_id:int,request:Request,db: _orm.Session = Depends(get_db)):
    params={
       "org_id":org_id,
        "first_name":request.query_params.get("first_name",None),
        "mobile":request.query_params.get("mobile",None),
        "owner":request.query_params.get("owner",None),
        "status":request.query_params.get("status",None),
        "source":request.query_params.get("source",None),
        "search":request.query_params.get("search",None)

    }

    filtered_leads = await _services.get_leads(db,params=_schemas.LeadRead(**params))
    response_leads = [map_lead_to_response(lead) for lead in filtered_leads]
    return response_leads

def map_lead_to_response(lead) -> _schemas.ResponseLeadRead:
    return _schemas.ResponseLeadRead(
        first_name=lead.first_name,
        mobile=lead.mobile,
        status=lead.status,
        source=lead.source,
        owner=lead.username,
        lead_since=lead.lead_since
    )
    



