from typing import List
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, DataError
import app.Event.schema as _schemas
import sqlalchemy.orm as _orm
import app.Event.models as _models
import app.Event.service as _services
# from main import logger
import app.core.db.session as _database
import logging
import datetime

router = APIRouter()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/events/", response_model=_schemas.EventRead, tags=["Event Router"])
async def read_all_events(db: _orm.Session = Depends(get_db)):
    return _services.read_all_events(db)

@router.get("/events/{event_id}", response_model=_schemas.EventRead, tags=["Event Router"])
async def read_event_by_id(event_id: int, db: _orm.Session = Depends(get_db)):
    return _services.read_event_by_id(event_id, db)

@router.post("/events/create_event", response_model=_schemas.EventCreate, tags=["Event Router"])
async def create_event(event: _schemas.EventCreate, db: _orm.Session = Depends(get_db)):
    return _services.create_event(event, db)