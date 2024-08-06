import json
from typing import Annotated, List, Optional
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header, Query, Request, status
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

@router.post("/food", response_model=_schemas.FoodCreateResponse)
async def create_food(food: _schemas.FoodCreate, db: _orm.Session = Depends(get_db)):
    try:
        
        return await _services.create_food(food, db)
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Food already exists")
    except DataError as e:
        raise HTTPException(status_code=400, detail="Invalid data")

def get_filters(

    search_key: Annotated[str | None, Query(title="Search Key")] = None,
    category: Annotated[str | None, Query(title="Category (Enum)")] = None,
    total_nutrition: Annotated[int, Query(title="Total Nutrition")] = None,
    total_fat: Annotated[int, Query(title="Total Fat")] = None,
    sort_order: Annotated[str,Query(title="Sorting Order")] = 'desc',
    limit: Annotated[int, Query(description="Pagination Limit")] = None,
    offset: Annotated[int, Query(description="Pagination offset")] = None
):
    return _schemas.FoodFilterParams(
        search_key=search_key,
        category=category,
        total_nutrition=total_nutrition,
        total_fat=total_fat,
        sort_order=sort_order,
        limit=limit,
        offset = offset
    )

@router.get("/food")
async def get_all_foods(org_id:int, filters: Annotated[_schemas.FoodFilterParams, Depends(get_filters)] = None, db: _orm.Session = Depends(get_db)):
    try:
        
        return await _services.get_food_by_org_id(db=db,org_id=org_id,params=filters)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/food/list/{org_id}",response_model=List[_schemas.FoodListResponse])
async def get_all_food_list(org_id:int, db: _orm.Session = Depends(get_db)):
    try:
        
        return await _services.get_all_foods(db=db,org_id=org_id)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/food/{id}", response_model=_schemas.FoodRead)
async def get_food_by_id(id: int, db: _orm.Session = Depends(get_db)):
    try:
        
        return await _services.get_food_by_id(id, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/food", response_model=_schemas.FoodCreateResponse)
async def update_food(food: _schemas.FoodUpdate, db: _orm.Session = Depends(get_db)):
    try:
        
        return await _services.update_food(food, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/food/{id}")
async def delete_food(id: int, db: _orm.Session = Depends(get_db)):
    try:
        
        await _services.delete_food(id, db)
        return {
            "id": id,
            "status_code": 200,
            "message": "Food deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))