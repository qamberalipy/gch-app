from typing import List
from fastapi import FastAPI, Header,APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, DataError
import app.Membership.schema as _schemas
import sqlalchemy.orm as _orm
import app.Membership.models as _models
import app.Membership.service as _services
# from main import logger
import app.core.db.session as _database
import pika
import logging
import datetime
import app.Shared.helpers as _helpers
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
        
@router.post("/register", response_model=_schemas.MembershipPlanRead)
async def register_membership_plan(plan: _schemas.MembershipPlanCreate, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        return _services.create_membership_plan(db=db, plan=plan)
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    
@router.get("/get_all/{org_id}", response_model=List[_schemas.MembershipPlanRead])
async def read_membership_plans(org_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:    
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        plans = _services.get_membership_plans_by_org_id(db=db, org_id=org_id)
        if not plans:
            return []
        return plans
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
  
    
@router.post("/credits", response_model=_schemas.CreditRead, tags=["Credits APIs"])
def create_credit(credit: _schemas.CreditCreate, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:    
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        return _services.create_credit(credit, db)
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.put("/credits", response_model=_schemas.CreditRead, tags=["Credits APIs"])
def update_credit(credit_id: int, credit: _schemas.CreditUpdate, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:    
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        
        db_credit = _services.update_credit(credit_id, credit, db)
        if db_credit is None:
            raise HTTPException(status_code=404, detail="Credit not found")
        return db_credit
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.delete("/credits", response_model=_schemas.CreditRead, tags=["Credits APIs"])
def delete_credit(credit_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:    
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        
        db_credit = _services.delete_credit(credit_id, db)
        if db_credit is None:
            raise HTTPException(status_code=404, detail="Credit not found")
        return db_credit
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.get("/credits", response_model=List[_schemas.CreditRead], tags=["Credits APIs"])
def get_credits_by_org_id(org_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:    
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        
        return _services.get_credits_by_org_id(org_id, db)
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    
@router.get("/credits/id", response_model=_schemas.CreditRead, tags=["Credits APIs"])
def get_credit_by_id(credit_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:    
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        
        db_credit = _services.get_credit_by_id(credit_id, db)
        if db_credit is None:
            raise HTTPException(status_code=404, detail="Credit not found")
        return db_credit
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
