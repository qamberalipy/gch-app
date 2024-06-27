from typing import List
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, DataError
import app.Coach.schema as _schemas
import sqlalchemy.orm as _orm
import app.Coach.models as _models
import app.Coach.service as _services
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
        

@router.post("/coaches/", response_model=_schemas.CoachRead, tags=["Coach Router"])
async def register_coach(coach: _schemas.CoachCreate, db: _orm.Session = Depends(get_db)):
    return _services.create_coach(db=db, coach=coach)

@router.get("/coaches/{org_id}", response_model=List[_schemas.CoachRead], tags=["Coach Router"])
async def read_coaches(org_id: int, db: _orm.Session = Depends(get_db)):
    coaches = _services.get_coaches_by_org_id(db=db, org_id=org_id)
    if not coaches:
        return []
    return coaches
