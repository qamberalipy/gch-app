from typing import List
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
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
async def register_membership_plan(plan: _schemas.MembershipPlanCreate, db: _orm.Session = Depends(get_db)):
    return _services.create_membership_plan(db=db, plan=plan)

@router.get("/get_all/{org_id}", response_model=List[_schemas.MembershipPlanRead])
async def read_membership_plans(org_id: int, db: _orm.Session = Depends(get_db)):
    plans = _services.get_membership_plans_by_org_id(db=db, org_id=org_id)
    if not plans:
       return []
    return plans