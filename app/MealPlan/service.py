import sqlalchemy.orm as _orm
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.MealPlan.schema as _schemas
import app.MealPlan.models as _models
import app.Shared.helpers as _helpers
import app.Food.models as _foodmodel
from typing import List
from sqlalchemy import func, or_ ,asc, desc, cast, String, text
from sqlalchemy.sql import and_  
from sqlalchemy.orm import aliased
from fastapi import FastAPI, Header,APIRouter, Depends, HTTPException, Request, status
from app.Exercise.service import extract_columns
from datetime import datetime


def create_database():
    return _database.Base.metadata.create_all(bind=_database.engine)

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def get_meal_plan_by_id(id: int, db: _orm.Session):

    member_ids_subquery = db.query(
        func.array_agg(_models.MemberMealPlan.member_id)
    ).filter(
        _models.MemberMealPlan.meal_plan_id == id
    ).scalar_subquery()

    # Main query to get the meal plan details and associated meals
    query = db.query(
        _models.MealPlan.id.label('meal_plan_id'),
        _models.MealPlan.name,
        _models.MealPlan.profile_img,
        _models.MealPlan.visible_for,
        _models.MealPlan.description,
        _models.MealPlan.org_id,
        _models.MealPlan.carbs,
        _models.MealPlan.protein,
        _models.MealPlan.fats,
        _models.MealPlan.created_by,
        _models.MealPlan.created_at,
        _models.MealPlan.updated_by,
        _models.MealPlan.updated_at,
        func.array_agg(
            func.json_build_object(
                'id', _models.Meal.id,
                'meal_time', _models.Meal.meal_time,
                'food_id', _models.Meal.food_id,
                'quantity', _models.Meal.quantity
            )
        ).label('meals'),
        member_ids_subquery.label('member_id')
    ).outerjoin(
        _models.Meal, _models.MealPlan.id == _models.Meal.meal_plan_id
    ).filter(
        _models.MealPlan.id == id,
        _models.MealPlan.is_deleted == False
    ).group_by(
        _models.MealPlan.id
    )
    db_meal_plan = query.first()

    if db_meal_plan is None:
        raise HTTPException(status_code=404, detail="Meal plan not found")    
    else:
        return db_meal_plan
    
def get_meal_plans_by_token(org_id: int, user_id : int, persona:str,  db: _orm.Session, params: _schemas.MealPlanFilterParams):
    
    sort_mapping = {
        "name": text("meal_plan.name"),
        "visible_for": text("meal_plan.visible_for"),
        "fats": text("meal_plan.fats"),
        "protein":text("meal_plan.protein"),
        "carbs":text("meal_plan.carbs"),
        "created_at": text("meal_plan.created_at")
    }
    
    filtered_member = db.query(
        _models.MemberMealPlan.meal_plan_id,func.array_agg(_models.MemberMealPlan.member_id).label('member_id')
    ).filter(
        _models.MemberMealPlan.meal_plan_id == _models.MealPlan.id
    ).group_by(_models.MemberMealPlan.meal_plan_id)

    if params.member_id:
        filtered_member = filtered_member.filter(
            _models.MemberMealPlan.member_id.in_(params.member_id))
    
    filtered_member=filtered_member.subquery()    
 
    filtered_meal_query = db.query(
        _models.MealPlan.id.label('meal_plan_id'),
        _models.MealPlan.name,
        _models.MealPlan.profile_img,
        _models.MealPlan.visible_for,
        _models.MealPlan.description,
        _models.MealPlan.org_id,
        _models.MealPlan.carbs,
        _models.MealPlan.protein,
        _models.MealPlan.fats,
        _models.MealPlan.persona,
        _models.MealPlan.created_by,
        _models.MealPlan.created_at,
        _models.MealPlan.updated_by,
        _models.MealPlan.updated_at,
        func.array_agg(
            func.json_build_object(
                'id', _models.Meal.id,
                'meal_time', _models.Meal.meal_time,
                'food_id', _models.Meal.food_id,
                'quantity', _models.Meal.quantity
            )
        ).label('meals')
        ).join(
            _models.Meal, _models.MealPlan.id == _models.Meal.meal_plan_id).filter(
            _models.MealPlan.org_id == org_id,
            _models.MealPlan.is_deleted == False
        ).group_by(
            _models.MealPlan.id)
    
    persona = 'member'
    if persona in ('member', 'Member'):
        filtered_meal_query = filtered_meal_query.filter(
        or_(_models.MealPlan.visible_for == 'everyone', _models.MealPlan.visible_for == 'members', and_(_models.MealPlan.visible_for == 'only_myself', _models.MealPlan.created_by == user_id)))
    elif persona in ('coach', 'Coach'):
        filtered_meal_query = filtered_meal_query.filter(or_(_models.MealPlan.visible_for == 'everyone',_models.MealPlan.visible_for == 'coaches', and_(_models.MealPlan.visible_for == 'only_myself', _models.MealPlan.created_by == user_id)))
        
    if params.search_key:
        search_pattern = f"%{params.search_key}%"
        filtered_meal_query = filtered_meal_query.filter(or_(
            _models.MealPlan.name.ilike(search_pattern),
            _models.MealPlan.description.ilike(search_pattern)))
        
    if params.created_by_me:
        filtered_meal_query = filtered_meal_query.filter(and_(_models.MealPlan.created_by == params.created_by_me, _models.MealPlan.persona == persona))
    
    if params.visible_for:
        filtered_meal_query = filtered_meal_query.filter(_models.MealPlan.visible_for == params.visible_for)
    
    if params.food_id:
        filtered_meal_query = filtered_meal_query.filter(_models.Meal.food_id.in_(params.food_id))
    
    if params.meal_time:
        filtered_meal_query = filtered_meal_query.filter(_models.Meal.meal_time == params.meal_time)
        
    if params.sort_key in sort_mapping.keys():
        sort_order = desc(sort_mapping.get(params.sort_key)) if params.sort_order == "desc" else asc(sort_mapping.get(params.sort_key))
        filtered_meal_query = filtered_meal_query.order_by(sort_order)
    elif params.sort_key is not None:
        raise _fastapi.HTTPException(status_code=400, detail="Sorting column not found.") 
    
    filtered_meal_query = filtered_meal_query.subquery()
        
    query=db.query( *[filtered_meal_query.c[column.name] for column in filtered_meal_query.columns],
                    filtered_member.c.member_id).join(filtered_member,filtered_member.c.meal_plan_id == filtered_meal_query.c.meal_plan_id)
    
    total_count_query = db.query(_models.MealPlan.id).filter(and_(_models.MealPlan.is_deleted == False, _models.MealPlan.org_id == org_id))
    total_counts = db.query(func.count()).select_from(total_count_query.subquery()).scalar()   
    
    filtered_counts = db.query(func.count()).select_from(query.subquery()).scalar()
    query = query.offset(params.offset).limit(params.limit)

    db_meal_plan = query.all()
    
    result = []
    for meal_plan in db_meal_plan:
        result.append({
            "meal_plan_id": meal_plan.meal_plan_id,
            "name": meal_plan.name,
            "profile_img": meal_plan.profile_img,
            "visible_for": meal_plan.visible_for,
            "description": meal_plan.description,
            "org_id": meal_plan.org_id,
            "carbs": meal_plan.carbs,
            "protein": meal_plan.protein,
            "fats": meal_plan.fats,
            "created_by": meal_plan.created_by,
            "created_at": meal_plan.created_at,
            "updated_by": meal_plan.updated_by,
            "updated_at": meal_plan.updated_at,
            "meals": meal_plan.meals,
            "member_id": meal_plan.member_id
        })
    
    if not db_meal_plan:
        result = []    
    
    return {"data":result,"total_counts":total_counts,"filtered_counts": filtered_counts}
   
        

def get_meal_plans_by_org_id(org_id: int, db: _orm.Session, persona:str ,params: _schemas.MealPlanFilterParams):
    
    sort_mapping = {
        "name": text("meal_plan.name"),
        "visible_for": text("meal_plan.visible_for"),
        "fats": text("meal_plan.fats"),
        "protein":text("meal_plan.protein"),
        "carbs":text("meal_plan.carbs"),
        "created_at": text("meal_plan.created_at")
    }
    
    filtered_member = db.query(
        _models.MemberMealPlan.meal_plan_id,func.array_agg(_models.MemberMealPlan.member_id).label('member_id')
    ).filter(
        _models.MemberMealPlan.meal_plan_id == _models.MealPlan.id
    ).group_by(_models.MemberMealPlan.meal_plan_id)

    if params.member_id:
        filtered_member = filtered_member.filter(
            _models.MemberMealPlan.member_id.in_(params.member_id))
    
    filtered_member=filtered_member.subquery()    
 
    filtered_meal_query = db.query(
        _models.MealPlan.id.label('meal_plan_id'),
        _models.MealPlan.name,
        _models.MealPlan.profile_img,
        _models.MealPlan.visible_for,
        _models.MealPlan.description,
        _models.MealPlan.org_id,
        _models.MealPlan.carbs,
        _models.MealPlan.protein,
        _models.MealPlan.fats,
        _models.MealPlan.persona,
        _models.MealPlan.created_by,
        _models.MealPlan.created_at,
        _models.MealPlan.updated_by,
        _models.MealPlan.updated_at,
        func.array_agg(
            func.json_build_object(
                'id', _models.Meal.id,
                'meal_time', _models.Meal.meal_time,
                'food_id', _models.Meal.food_id,
                'quantity', _models.Meal.quantity
            )
        ).label('meals')
        ).join(
            _models.Meal, _models.MealPlan.id == _models.Meal.meal_plan_id).filter(
            _models.MealPlan.org_id == org_id,
            _models.MealPlan.is_deleted == False
        ).group_by(
            _models.MealPlan.id)
    
    if params.search_key:
        search_pattern = f"%{params.search_key}%"
        filtered_meal_query = filtered_meal_query.filter(or_(
            _models.MealPlan.name.ilike(search_pattern),
            _models.MealPlan.description.ilike(search_pattern)))
        
    if params.created_by_me:
        filtered_meal_query = filtered_meal_query.filter(and_(_models.MealPlan.created_by == params.created_by_me, _models.MealPlan.persona == persona))
    
    if params.visible_for:
        filtered_meal_query = filtered_meal_query.filter(_models.MealPlan.visible_for == params.visible_for)
    
    if params.food_id:
        filtered_meal_query = filtered_meal_query.filter(_models.Meal.food_id.in_(params.food_id))
    
    if params.meal_time:
        filtered_meal_query = filtered_meal_query.filter(_models.Meal.meal_time == params.meal_time)
        
    if params.sort_key in sort_mapping.keys():
        sort_order = desc(sort_mapping.get(params.sort_key)) if params.sort_order == "desc" else asc(sort_mapping.get(params.sort_key))
        filtered_meal_query = filtered_meal_query.order_by(sort_order)
    elif params.sort_key is not None:
        raise _fastapi.HTTPException(status_code=400, detail="Sorting column not found.") 
    
    filtered_meal_query = filtered_meal_query.subquery()
        
    query=db.query( *[filtered_meal_query.c[column.name] for column in filtered_meal_query.columns],
                    filtered_member.c.member_id).join(filtered_member,filtered_member.c.meal_plan_id == filtered_meal_query.c.meal_plan_id)
    
    total_count_query = db.query(_models.MealPlan.id).filter(and_(_models.MealPlan.is_deleted == False, _models.MealPlan.org_id == org_id))
    total_counts = db.query(func.count()).select_from(total_count_query.subquery()).scalar()   
    
    filtered_counts = db.query(func.count()).select_from(query.subquery()).scalar()
    query = query.offset(params.offset).limit(params.limit)

    db_meal_plan = query.all()
    
    result = []
    for meal_plan in db_meal_plan:
        result.append({
            "meal_plan_id": meal_plan.meal_plan_id,
            "name": meal_plan.name,
            "profile_img": meal_plan.profile_img,
            "visible_for": meal_plan.visible_for,
            "description": meal_plan.description,
            "org_id": meal_plan.org_id,
            "carbs": meal_plan.carbs,
            "protein": meal_plan.protein,
            "fats": meal_plan.fats,
            "created_by": meal_plan.created_by,
            "created_at": meal_plan.created_at,
            "updated_by": meal_plan.updated_by,
            "updated_at": meal_plan.updated_at,
            "meals": meal_plan.meals,
            "member_id": meal_plan.member_id
        })
    
    if not db_meal_plan:
        result = []    
    
    return {"data":result,"total_counts":total_counts,"filtered_counts": filtered_counts}
   
def create_meal_plan(meal_plan: _schemas.CreateMealPlan,user_id,persona,db: _orm.Session):

    meal_plan_dict = meal_plan.dict(exclude={'meals','member_id'})
    meal_plan_dict['created_by']=user_id
    meal_plan_dict['updated_by']=user_id
    meal_plan_dict['persona']=persona
    meal_plan_dict['created_at']=datetime.now()
    meal_plan_dict['updated_at']=datetime.now()
    
    db_meal_plan = _models.MealPlan(**meal_plan_dict)
    db.add(db_meal_plan)
    db.commit()
    db.refresh(db_meal_plan)
    return db_meal_plan

def create_member_meal_plan(meal_plan_id : int, member_ids: List[int], db: _orm.Session):
    member_meal_plans = [
        _models.MemberMealPlan(meal_plan_id=meal_plan_id, member_id=member_id)
        for member_id in member_ids
    ]

    db.add_all(member_meal_plans)
    db.commit()

    return member_meal_plans

def update_meal_plan(meal_plan_id: int,user_id,meal_plan: _schemas.UpdateMealPlan, db: _orm.Session):
    try:
        # Retrieve the existing meal plan
        db_meal_plan = db.query(_models.MealPlan).filter(_models.MealPlan.id == meal_plan_id, 
                                _models.MealPlan.is_deleted == False).first()
        if not db_meal_plan:
            return None
     
        # Update meal plan details
        for key, value in meal_plan.dict(exclude={'meals', 'member_id'}, exclude_unset=True).items():
            setattr(db_meal_plan, key, value)

        if meal_plan.meals:
            # Retrieve existing meals and member meal plans
            existing_meals = db.query(_models.Meal).filter(_models.Meal.meal_plan_id == meal_plan_id).all()
        
            # Create dictionaries for easy lookup
            existing_meal_map = {(meal.meal_time, meal.food_id): meal for meal in existing_meals}
            new_meal_map = {(meal.meal_time, meal.food_id): meal for meal in meal_plan.meals}

            # Identify meals to be deleted and added/updated
            meals_to_delete = [meal for key, meal in existing_meal_map.items() if key not in new_meal_map]
            meals_to_add_or_update = []

            for key, new_meal in new_meal_map.items():
                if key in existing_meal_map:
                    existing_meal = existing_meal_map[key]
                    if existing_meal.quantity != new_meal.quantity:
                        existing_meal.quantity = new_meal.quantity
                else:
                    meals_to_add_or_update.append(_models.Meal(
                        meal_time=new_meal.meal_time,
                        food_id=new_meal.food_id,
                        quantity=new_meal.quantity,
                        meal_plan_id=meal_plan_id
                    ))

            if meals_to_delete:
                db.query(_models.Meal).filter(
                    _models.Meal.meal_plan_id == meal_plan_id,
                    _models.Meal.food_id.in_([meal.food_id for meal in meals_to_delete]),
                    _models.Meal.meal_time.in_([meal.meal_time for meal in meals_to_delete])
                ).delete(synchronize_session=False)

            if meals_to_add_or_update:
                db.bulk_save_objects(meals_to_add_or_update)

        if meal_plan.member_id: 
        # Update member meal plans
            existing_member_meal_plans = db.query(_models.MemberMealPlan).filter(_models.MemberMealPlan.meal_plan_id == meal_plan_id).all()
        
            existing_member_ids = {mmp.member_id for mmp in existing_member_meal_plans}
            new_member_ids = set(meal_plan.member_id)

            members_to_delete = existing_member_ids - new_member_ids
            members_to_add = new_member_ids - existing_member_ids

            if members_to_delete:
                db.query(_models.MemberMealPlan).filter(
                    _models.MemberMealPlan.meal_plan_id == meal_plan_id,
                    _models.MemberMealPlan.member_id.in_(members_to_delete)
                ).delete(synchronize_session=False)

            if members_to_add:
                db.bulk_save_objects([_models.MemberMealPlan(
                    meal_plan_id=meal_plan_id,
                    member_id=member_id
                ) for member_id in members_to_add])

        db_meal_plan.updated_by=user_id
        db_meal_plan.updated_at=datetime.now()
        db.commit()
        db.refresh(db_meal_plan)
        return db_meal_plan
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred while updating the meal plan: {str(e)}")
    finally:
        db.close()

def delete_meal_plan(meal_plan_id: int, user_id: int, db: _orm.Session = _fastapi.Depends(get_db)):
    db_meal_plan = db.query(_models.MealPlan).filter(_models.MealPlan.id == meal_plan_id).first()
    if db_meal_plan:
        db_meal_plan.is_deleted = True
        db_meal_plan.updated_by = user_id
        db_meal_plan.updated_at = datetime.now()
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

