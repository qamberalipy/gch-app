from typing import Annotated, List
from fastapi import Header,FastAPI, APIRouter, Depends, HTTPException, Request, status
# from sqlalchemy import Tuple
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
import app.Shared.helpers as _helpers
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

@router.post("/coach", response_model=SharedCreateSchema,tags=["Coach API"])
async def create_coach(coach: _schemas.CoachCreate, db: _orm.Session = Depends(get_db)):
    
    if not _helpers.validate_email(coach.email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    return await _services.create_coach(coach,db)

@router.put("/coach",response_model = _schemas.CoachUpdate,tags=["Coach API"])
async def update_coach(coach: _schemas.CoachUpdate, db: _orm.Session = Depends(get_db)):
    db_coach = await _services.update_coach(coach.id,coach,"web",db)
    if db_coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return db_coach

@router.delete("/coach/{id}",response_model=SharedModifySchema, tags=["Coach API"])
def delete_coach(id:int, db: _orm.Session = Depends(get_db)):
    db_coach = _services.delete_coach(id,db)
    if db_coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return db_coach

@router.get("/coach/{id}", response_model=_schemas.CoachReadSchema, tags=["Coach API"])
def get_coach_by_id(id: int, db: _orm.Session = Depends(get_db)):
    db_coach = _services.get_coach_by_id(id, db)
    if db_coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return db_coach

@router.get("/coach/list/{org_id}", response_model=List[_schemas.CoachList],tags=["Coach API"])
async def get_coach(org_id,db: _orm.Session = Depends(get_db)):
    try:
            
        coaches = _services.get_coach_list(org_id,db=db)
        return coaches
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.get("/coach", tags=["Coach API"])
def get_coaches_by_org_id(org_id: int,filters: Annotated[_schemas.CoachFilterParams, Depends(_services.get_filters)] = None,db: _orm.Session = Depends(get_db)):
    coaches = _services.get_all_coaches_by_org_id(org_id, db, params=filters)
    return coaches


@router.get("/coach/count/{org_id}", response_model=_schemas.CoachCount, tags=["Coach API"])
async def get_total_coaches(org_id: int, db: _orm.Session = Depends(get_db)):
    try:
        total_coaches = await _services.get_total_coaches(org_id, db)
        return {"total_coaches": total_coaches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
