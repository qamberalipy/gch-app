import sqlalchemy.orm as _orm
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.MealPlan.schema as _schemas
import app.MealPlan.models as _models
import app.Shared.helpers as _helpers
from typing import List
from sqlalchemy import func, or_
from sqlalchemy.sql import and_  
from fastapi import FastAPI, Header,APIRouter, Depends, HTTPException, Request, status

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

def create_meal_plan(meal_plan: _schemas.CreateMealPlan, db: _orm.Session):
    # Remove the 'meals' field from the meal plan dictionary if it exists
    meal_plan_dict = meal_plan.dict(exclude={'meals'})
    db_meal_plan = _models.MealPlan(**meal_plan_dict)
    db.add(db_meal_plan)
    db.commit()
    db.refresh(db_meal_plan)
    return db_meal_plan

def update_meal_plan(meal_plan_id: int, meal_plan: _schemas.UpdateMealPlan, db: _orm.Session):
    # Retrieve the existing meal plan
    db_meal_plan = db.query(_models.MealPlan).filter(_models.MealPlan.id == meal_plan_id).first()
    if not db_meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    # Update meal plan details
    for key, value in meal_plan.dict(exclude={'meals'}, exclude_unset=True).items():
        setattr(db_meal_plan, key, value)

    # Remove existing meals
    db.query(_models.Meal).filter(_models.Meal.meal_plan_id == meal_plan_id).delete()

    # Add updated meals
    updated_meals = [
        _models.Meal(
            meal_time=meal.meal_time,
            food_id=meal.food_id,
            quantity=meal.quantity,
            meal_plan_id=meal_plan_id
        ) for meal in meal_plan.meals
    ]

    db.add_all(updated_meals)
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

def create_meal(meal_plan_id: int, meals: List[_schemas.CreateMeal], db: _orm.Session):
    db_meals = [
        _models.Meal(
            meal_time=meal.meal_time,
            food_id=meal.food_id,
            quantity=meal.quantity,
            meal_plan_id=meal_plan_id
        ) for meal in meals
    ]
    
    db.add_all(db_meals)
    db.commit()

    return db_meals

def delete_meal(meal_id: int, db: _orm.Session = _fastapi.Depends(get_db)):
    db_meal = db.query(_models.Meal).filter(_models.Meal.id == meal_id).first()
    if db_meal:
        db_meal.is_deleted = True
        db.commit()
        db.refresh(db_meal)
    return db_meal