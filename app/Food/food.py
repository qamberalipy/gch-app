import json
from typing import List, Optional
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.exc import IntegrityError, DataError
import app.Food.schema as _schemas
import sqlalchemy.orm as _orm
import app.Food.models as _models
import app.Food.service as _services
import app.core.db.session as _database
import pika
import fastapi as _fastapi
import logging
import datetime
import app.Shared.helpers as _helpers

router = APIRouter(tags=["Food Router"])

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=_schemas.FoodCreateResponse)
async def create_food(food: _schemas.FoodCreate, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        return await _services.create_food(food, db)
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Food already exists")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Invalid data")

@router.get("/", response_model=List[_schemas.FoodRead])
async def get_all_foods(db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        return await _services.get_all_foods(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{food_id}", response_model=_schemas.FoodRead)
async def get_food_by_id(food_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        return await _services.get_food_by_id(food_id, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/", response_model=_schemas.FoodCreateResponse)
async def update_food(food: _schemas.FoodUpdate, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        return await _services.update_food(food, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{food_id}")
async def delete_food(food_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        _helpers.verify_jwt(authorization, "User")
        await _services.delete_food(food_id, db)
        return {
            "id": food_id,
            "status_code": 200,
            "message": "Food deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))