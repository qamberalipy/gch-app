import sqlalchemy.orm as _orm
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.MealPlan.schema as _schemas
import app.MealPlan.models as _models
import app.Shared.helpers as _helpers
from typing import List
from sqlalchemy import func, or_ ,asc, desc, cast, String
from sqlalchemy.sql import and_  
from sqlalchemy.orm import aliased
from fastapi import FastAPI, Header,APIRouter, Depends, HTTPException, Request, status

def create_database():
    return _database.Base.metadata.create_all(bind=_database.engine)

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def get_meal_plan_by_id(id: int, db: _orm.Session):
    query = db.query(
        _models.MealPlan.id,
        _models.MealPlan.name,
        _models.MealPlan.profile_img,
        _models.MealPlan.visible_for,
        _models.MealPlan.description,
        _models.MealPlan.org_id,
        func.array_agg(
            func.json_build_object(
                'id', _models.Meal.id,
                'meal_time', _models.Meal.meal_time,
                'food_id', _models.Meal.food_id,
                'quantity', _models.Meal.quantity
            )
        ).label('meals')
    ).outerjoin(
        _models.Meal, _models.MealPlan.id == _models.Meal.meal_plan_id
    ).filter(
        _models.MealPlan.id == id,
        _models.MealPlan.is_deleted == False
    ).group_by(
        _models.MealPlan.id,
        _models.MealPlan.name,
        _models.MealPlan.org_id,
        _models.MealPlan.profile_img,
        _models.MealPlan.visible_for,
        _models.MealPlan.description,
    )

    db_meal_plan = query.first()
    
    if db_meal_plan is None:
        raise HTTPException(status_code=404, detail="Meal plan not found")    
    else:
        return db_meal_plan
    
def get_meal_plans_by_org_id(org_id: int, db: _orm.Session,params: _schemas.MealPlanFilterParams):
    
    sort_order = desc(_models.MealPlan.created_at) if params.sort_order == "desc" else asc(_models.MealPlan.created_at)
    
    query = db.query(
        _models.MealPlan.id,
        _models.MealPlan.name,
        _models.MealPlan.profile_img,
        _models.MealPlan.visible_for,
        _models.MealPlan.description,
        _models.MealPlan.org_id,
        func.array_agg(
            func.json_build_object(
                'id', _models.Meal.id,
                'meal_time', _models.Meal.meal_time,
                'food_id', _models.Meal.food_id,
                'quantity', _models.Meal.quantity
            )
        ).label('meals')
    ).join(
        _models.Meal, _models.MealPlan.id == _models.Meal.meal_plan_id
    ).filter(
        _models.MealPlan.org_id == org_id,
        _models.MealPlan.is_deleted == False
    ).order_by(sort_order
    ).group_by(
        _models.MealPlan.id
        )
    
    if params.search_key:
        search_pattern = f"%{params.search_key}%"
        query = query.filter(or_(
            _models.MealPlan.name.ilike(search_pattern),
            _models.MealPlan.description.ilike(search_pattern),
            _models.Meal.meal_time.ilike(search_pattern)
        ))
            
    if params.visible_for:
        query = query.filter(cast(_models.MealPlan.visible_for, String).ilike(f"%{params.visible_for}%"))
        print("query1", query)
    
    if params.assign_to:
        query = query.filter(_models.MealPlan.assign_to.ilike(f"%{params.assign_to}%"))
    
    query = query.offset(params.offset).limit(params.limit)
    db_mealplan = query.all()

    print("query",db_mealplan)
    return db_mealplan
   
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