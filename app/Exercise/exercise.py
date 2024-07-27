from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.exc import IntegrityError, DataError
import app.Exercise.schema as _schemas
import sqlalchemy.orm as _orm
import app.Exercise.service as _services
import app.core.db.session as _database
import logging
import app.Shared.helpers as _helpers

router = APIRouter(tags=["Exercise Router"])

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/exercise", response_model=List[_schemas.Muscle])
async def get_muscle(db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
    
        filtered_leads = await _services.get_muscle(db)
        return filtered_leads
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")        
    

@router.post("/exercise",response_model=_schemas.ExerciseCreate)
async def create_exercise(exercise: _schemas.ExerciseCreate, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        
        new_exercise = await _services.create_exercise(exercise,db)
        return new_exercise

    except DataError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data error occurred, check your input") 