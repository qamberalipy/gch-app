from typing import List
from sqlalchemy import func, or_
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.MealPlan.schema as _schemas
import app.MealPlan.models as _models
import app.Shared.helpers as _helpers

def create_database():
    return _database.Base.metadata.create_all(bind=_database.engine)

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

def get_meal_plan(meal_plan_id: int, db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(_models.MealPlan).filter(_models.MealPlan.id == meal_plan_id).first()

def create_meal_plan(meal_plan: _schemas.CreateMealPlan, db: _orm.Session = _fastapi.Depends(get_db)):
    db_meal_plan = _models.MealPlan(**meal_plan.dict())
    db.add(db_meal_plan)
    db.commit()
    db.refresh(db_meal_plan)
    return db_meal_plan

def update_meal_plan(meal_plan: _schemas.UpdateMealPlan, db: _orm.Session = _fastapi.Depends(get_db)):
    db_meal_plan = db.query(_models.MealPlan).filter(_models.MealPlan.id == meal_plan.id).first()
    if db_meal_plan:
        for key, value in meal_plan.dict(exclude_unset=True).items():
            setattr(db_meal_plan, key, value)
        db.commit()
        db.refresh(db_meal_plan)
    return db_meal_plan

def delete_meal_plan(meal_plan_id: int,  db: _orm.Session = _fastapi.Depends(get_db)):
    db_meal_plan = db.query(_models.MealPlan).filter(_models.MealPlan.id == meal_plan_id).first()
    if db_meal_plan:
        db_meal_plan.is_deleted = True
        db.commit()
        db.refresh(db_meal_plan)
    return db_meal_plan

# CRUD operations for Meal
def get_meal(meal_id: int, db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(_models.Meal).filter(_models.Meal.id == meal_id).first()

def create_meal(meal: _schemas.CreateMeal, db: _orm.Session = _fastapi.Depends(get_db)):
    db_meal = _models.Meal(**meal.dict())
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal

def update_meal(meal: _schemas.UpdateMeal, db: _orm.Session = _fastapi.Depends(get_db)):
    db_meal = db.query(_models.Meal).filter(_models.Meal.id == meal.id).first()
    if db_meal:
        for key, value in meal.dict(exclude_unset=True).items():
            setattr(db_meal, key, value)
        db.commit()
        db.refresh(db_meal)
    return db_meal

def delete_meal(meal_id: int, db: _orm.Session = _fastapi.Depends(get_db)):
    db_meal = db.query(_models.Meal).filter(_models.Meal.id == meal_id).first()
    if db_meal:
        db_meal.is_deleted = True
        db.commit()
        db.refresh(db_meal)
    return db_meal