from typing import List
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

@router.post("/mobile/register", response_model=_schemas.CoachRead ,tags=["App Router"])
def create_mobilecoach(coach: _schemas.CoachAppBase, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing access token")
    _helpers.verify_jwt(authorization, "User")
    return _services.create_appcoach(coach,db)


@router.post("/login", response_model=_schemas.CoachLoginResponse,  tags=["App Router"])
async def login_coach(coach_data: _schemas.CoachLogin, db: _orm.Session = Depends(get_db)):
    try:
        print(coach_data)
        result = await _services.login_coach(coach_data.email_address, coach_data.wallet_address, db)
        print(result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    

@router.post("/coaches", response_model=_schemas.CoachRead ,tags=["Coach API"])
def create_coach(coach: _schemas.CoachCreate, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing access token")
    _helpers.verify_jwt(authorization, "User")
    return _services.create_coach(coach,db)

@router.put("/coaches", response_model=_schemas.CoachRead , tags=["Coach API"])
def update_coach(coach: _schemas.CoachUpdate, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing access token")
    _helpers.verify_jwt(authorization, "User")
    db_coach = _services.update_coach(coach,db)
    if db_coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return db_coach

@router.delete("/coaches", response_model=_schemas.CoachRead, tags=["Coach API"])
def delete_coach(coach: _schemas.CoachDelete, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing access token")
    _helpers.verify_jwt(authorization, "User")
    db_coach = _services.delete_coach(coach.id,db)
    if db_coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return db_coach

@router.get("/coaches", response_model=_schemas.CoachReadSchema, tags=["Coach API"])
def get_coach_by_id(coach_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing access token")
    _helpers.verify_jwt(authorization, "User")
    db_coach = _services.get_coach_by_id(coach_id,db)
    if db_coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return db_coach

@router.get("/coaches/getAll", response_model=List[_schemas.CoachRead], tags=["Coach API"])
def get_coaches_by_org_id(org_id: int,request: Request,db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing access token")
    _helpers.verify_jwt(authorization, "User")
    print("MY LIST ",Request)
    params = {
        "org_id": org_id,
        "search_key": request.query_params.get("search_key"),
        "sort_by": request.query_params.get("sort_by"),
        "status": request.query_params.get("status"),
        "limit":request.query_params.get('limit') ,
        "offset":request.query_params.get('offset')
    }
    print(params)
    coaches = _services.get_all_coaches_by_org_id(db,params=_schemas.CoachFilterParams(**params))
    return coaches



@router.get("/getTotalCoach", response_model=_schemas.CoachCount, tags=["Coach Router"])
async def get_total_coaches(org_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        
        total_coaches = await _services.get_total_coaches(org_id, db)
        return {"total_coaches": total_coaches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")