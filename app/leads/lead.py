from typing import List
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
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
        
    
@router.post("/register/lead", response_model=_schemas.LeadCreate,tags=["Lead Router"])
async def register_lead(lead_data: _schemas.LeadCreate, db: _orm.Session = Depends(get_db)):   
    try:
        new_lead = await _services.create_lead(_schemas.LeadCreate(**lead_data), db)
        return new_lead

    except DataError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")



# @router.get("/clients/{client_id}", response_model=_schemas.ClientRead)
# async def get_client(client_id: int, db: _orm.Session = Depends(get_db)):
    # client = await _services.get_client_by_id(client_id, db)
    # if not client:
        # raise HTTPException(status_code=404, detail="Client not found")
    # return client

# @router.post("/register/business/", response_model=_schemas.BusinessRead)
# async def register_business(business: _schemas.BusinessCreate,db: _orm.Session = Depends(get_db)):
#     return _services.create_business(db=db, business=business)

# @router.get("/get_all_business/{org_id}", response_model=List[_schemas.BusinessRead])
# async def read_businesses(org_id: int,db: _orm.Session = Depends(get_db)):
#     businesses = _services.get_businesses_by_org_id(db=db, org_id=org_id)
#     if not businesses:
#         raise HTTPException(status_code=404, detail="No businesses found for this organization")
#     return businesses


