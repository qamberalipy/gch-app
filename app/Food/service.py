from datetime import date

import datetime
from typing import Annotated,Any, List
import jwt
from sqlalchemy import String, asc, cast, desc, func, literal_column, or_, text
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Food.schema as _schemas
import app.Food.models as _models
import app.user.models as _usermodels
import app.Shared.helpers as _helpers
import random
import json
import pika
import time
import os
import bcrypt as _bcrypt
from . import models, schema
from sqlalchemy.orm import aliased


async def create_food(food: _schemas.FoodCreate, db: _orm.Session):
    print(food)
    db_food = _models.Food(**food.dict())
    print("Db Food", db_food)
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food



async def get_food_by_id(food_id: int, db: _orm.Session):
    return db.query(_models.Food).filter(_models.Food.id == food_id).first()

async def update_food(food: _schemas.FoodUpdate, db: _orm.Session):
    db_food = db.query(_models.Food).filter(_models.Food.id == food.id).first()
    if db_food is None:
        return _fastapi.HTTPException(status_code=404, detail="Food not found")
    update_data = food.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_food, key, value)
    db_food.updated_at = datetime.datetime.now()
    db.commit()
    db.refresh(db_food)
    
    return db_food


async def delete_food(food_id: int, db: _orm.Session):
    db_food = db.query(_models.Food).filter(_models.Food.id == food_id).first()
    if db_food is None:
        return _fastapi.HTTPException(status_code=404, detail="Food not found")
    db.delete(db_food)
    db.commit()
    return db_food

async def get_all_foods(db: _orm.Session,org_id:int):
    return db.query(_models.Food.id,_models.Food.name,_models.Food.img_url,_models.Food.is_validated).filter(
            _models.Food.org_id == org_id).order_by(
            desc(_models.Food.created_at)).all()

async def get_food_by_org_id(db: _orm.Session,org_id: int,params: _schemas.FoodFilterParams):
    
    sort_mapping = {
        "name": text("foods.name"),
        "brand":text("foods.brand"),
        "total_nutrition": text("foods.total_nutrition"),
        "category" : text("foods.category"),
        "fat":text("foods.fat"),
        "created_at":text("foods.created_at")
        }

    query = db.query(_models.Food).filter(_models.Food.org_id == org_id)
    total_counts = db.query(func.count()).select_from(query.subquery()).scalar()

    if params.search_key:
        query = query.filter(
            or_(_models.Food.name.ilike(f"%{params.search_key}%"))
        )
    
    if params.category:
        query = query.filter(_models.Food.category == params.category)
    
    if params.total_nutrition:
        query = query.filter(
            _models.Food.total_nutrition >= params.total_nutrition
        )
        
    if params.total_fat:
        query = query.filter(
            _models.Food.fat >= params.total_fat
        )
    
    if params.sort_key in sort_mapping.keys():       
            sort_order = desc(sort_mapping.get(params.sort_key)) if params.sort_order == "desc" else asc(sort_mapping.get(params.sort_key))
            query=query.order_by(sort_order)
            
    elif params.sort_key is not None:
        raise _fastapi.HTTPException(status_code=400, detail="Sorting column not found.")
    
    filtered_counts = db.query(func.count()).select_from(query.subquery()).scalar()
    
    query=query.limit(params.limit).offset(params.offset)
    
    db_foods = query.all()
    
    foods = []
    for food in db_foods:
        foods.append(food)

    
    return {"data":foods,"total_counts":total_counts,"filtered_counts": filtered_counts}
    