from typing import Annotated, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Header,Request
from fastapi.security import OAuth2PasswordBearer
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


@router.get("/exercise/muscles", response_model=List[_schemas.Muscle])
async def get_muscle(db: _orm.Session = Depends(get_db)):
    try:
            
        muscles = await _services.get_muscle(db)
        return muscles
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")        
    

@router.get("/exercise/met", response_model=List[_schemas.Met])
async def get_met(db: _orm.Session = Depends(get_db)):
    try:  
        met = await _services.get_met(db)
        return met
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.get("/exercise/equipments", response_model=List[_schemas.Equipments],summary="Get Equipments")
async def get_muscle(db: _orm.Session = Depends(get_db)):
    try:
        equipments = await _services.get_equipments(db)
        return equipments
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")

@router.get("/exercise/category", response_model=List[_schemas.Category])
async def get_category(db: _orm.Session = Depends(get_db)):
    try:
        categories = await _services.get_category(db)
        return categories
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")    

@router.get("/exercise/primary_joints", response_model=List[_schemas.PrimaryJoint],summary="Get Primary Joints")
async def get_muscle(db: _orm.Session = Depends(get_db)):
    try:
    
        primary_joints = await _services.get_primary_joints(db)
        return primary_joints
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data` error occurred, check your input")


@router.post("/exercise")
async def create_exercise(exercise: _schemas.ExerciseCreate,request:Request,db: _orm.Session = Depends(get_db)):
    try:
        user_id=request.state.user.get('id')
        user_type=request.state.user.get('user_type')
        new_exercise = await _services.create_exercise(exercise,user_id,user_type,db)
        return {
            "status_code": "201",
            "id": new_exercise,
            "message": "Exercise created successfully"
        }

    except DataError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data error occurred, check your input") 
    

@router.get("/exercise", response_model=Union[List[_schemas.ExerciseRead],_schemas.GetAllResponse])
async def get_exercise(org_id:int,request:Request,filters: Annotated[_schemas.ExerciseFilterParams, Depends(_services.get_filters)] = None,db: _orm.Session = Depends(get_db)):
    
    user_type=request.state.user.get('user_type')
    exercises = await _services.get_exercise(org_id=org_id,params=filters,user_type=user_type,db=db)
    return exercises   

@router.get("/exercise/{id}", response_model=_schemas.ExerciseRead,summary="Get Exercise By ID")
async def get_exercise(id:int,db: _orm.Session = Depends(get_db)):
    
    exercises = await _services.get_exercise(id=id,db=db)
    return exercises   

@router.put("/exercise")
async def update_exercise(data:_schemas.ExerciseUpdate,request:Request,db: _orm.Session = Depends(get_db)):
    user_id=request.state.user.get('id')
    user_type=request.state.user.get('user_type')
    exercises = await _services.exercise_update(data,user_id,user_type,db)
    return exercises

@router.delete("/exercise/{id}",summary="Delete Exercise")
async def delete_exercise(id:int,request:Request,db: _orm.Session = Depends(get_db)):
    user_id=request.state.user.get('id')
    user_type=request.state.user.get('id')
    db_exercise = await _services.delete_exercise(id,user_id,user_type,db)
    return db_exercise