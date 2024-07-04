from typing import List
from fastapi import Header,FastAPI, APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, DataError
import app.Event.schema as _schemas
import sqlalchemy.orm as _orm
import app.Event.models as _models
import app.Event.service as _services
import app.Shared.helpers as _helpers
# from main import logger
import app.core.db.session as _database
import logging
import datetime

router = APIRouter(tags=["Event Router"])


logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# @router.post("/get_events/", response_model=_schemas.EventRead, tags=["Event Router"])
# async def read_all_events(db: _orm.Session = Depends(get_db)):
#     return _services.read_all_events(db)

# @router.get("/get_event/{event_id}", response_model=_schemas.EventRead, tags=["Event Router"])
# async def read_event_by_id(event_id: int, db: _orm.Session = Depends(get_db)):
#     return _services.read_event_by_id(event_id, db)

@router.post("/create_event", response_model=_schemas.EventCreate)
async def create_event(event: _schemas.EventCreate,db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        
        return _services.create_event(event, db)
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.post("/update_event/{event_id}", response_model=_schemas.EventUpdate)
async def update_event(event_id: int, event: _schemas.EventUpdate,db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        return _services.update_event(event_id, event, db)
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.get("/get_events", response_model=List[_schemas.EventRead])
async def read_events(event_id: int = 0, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        if event_id != 0:
            return _services.read_event_by_id(event_id, db)
        return _services.read_all_events(db)
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")