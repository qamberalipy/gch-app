from datetime import date
import datetime
from typing import Optional
import jwt
from sqlalchemy import desc, func, or_
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Food.schema as _schemas
import app.Food.models as _models
import random
import json
import pika
import time
import os
import bcrypt as _bcrypt


async def create_food(food: _schemas.FoodCreate, db: _orm.Session):
    print(food)
    db_food = _models.Food(**food.dict())
    print("Db Food", db_food)
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food


async def get_all_foods(db: _orm.Session):
    return db.query(_models.Food).all()

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