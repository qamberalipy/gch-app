from typing import List, Annotated
from fastapi import FastAPI, Header,APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.exc import IntegrityError, DataError
import app.MealPlan.schema as _schemas
import sqlalchemy.orm as _orm
import app.MealPlan.service as _service
import app.MealPlan.models as _model
import app.core.db.session as _database
import logging
import app.Shared.helpers as _helpers

router = APIRouter(tags=["Meal Plan Router"])

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/meal_plans",response_model=_schemas.ReadMealPlan)
async def create_meal_plan(meal_plan: _schemas.CreateMealPlan,request:Request,db: _orm.Session = Depends(get_db)):
    try:
        user_id=request.state.user.get('id')
        persona = request.state.user.get('user_type')

        new_meal_plan = _service.create_meal_plan(meal_plan,user_id,persona,db)

        _service.create_meal(new_meal_plan.id,meal_plan.meals, db)
        _service.create_member_meal_plan(new_meal_plan.id, meal_plan.member_id,db)

        return new_meal_plan
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
   

@router.get("/meal_plans/{id}", response_model=_schemas.ShowMealPlan)
async def get_meal_plans(id:int , db: _orm.Session = Depends(get_db)):
    try:
        meal_plans = _service.get_meal_plan_by_id(id,db)    
        return meal_plans
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.put("/meal_plans", response_model=_schemas.ReadMealPlan)
async def update_meal_plan(meal_plan: _schemas.UpdateMealPlan,request:Request,db: _orm.Session = Depends(get_db)):
    try:
        user_id=request.state.user.get('id')
        updated_meal_plan = _service.update_meal_plan(meal_plan.id,user_id,meal_plan, db)
        
        if updated_meal_plan is None:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        else:
            return updated_meal_plan
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
   

@router.delete("/meal_plans/{id}", response_model=_schemas.ReadMealPlan)
async def delete_meal_plan(id:int, request:Request, db: _orm.Session = Depends(get_db)):
    try:
        user_id = request.state.user.get('id')
        deleted_meal_plan = _service.delete_meal_plan(id, user_id, db)
        if deleted_meal_plan is None:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        return deleted_meal_plan
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
       
def get_filters(

    search_key: Annotated[str | None, Query(title="Search Key")] = None,
    visible_for: Annotated[str | None, Query(title="visible for Enum")] = None,
    meal_time : Annotated[str | None, Query(title="Meal time")] = None,
    sort_key: Annotated[str | None, Query(title="Sort Key")] = None,
    sort_order: Annotated[str,Query(title="Sorting Order")] = 'desc',
    limit: Annotated[int, Query(description="Pagination Limit")] = None,
    offset: Annotated[int, Query(description="Pagination offset")] = None,
    member_id : Annotated[list[int], Query(description="Member Ids")] = [],
    food_id : Annotated[list[int], Query(description="Food Ids")] = [],
    created_by_me : Annotated[int | None, Query(title="Created by me")] = None,
):
    return _schemas.MealPlanFilterParams(
        search_key=search_key,
        visible_for=visible_for,
        meal_time = meal_time,
        sort_key=sort_key,
        sort_order=sort_order,
        member_id= member_id,
        food_id =food_id,
        limit=limit,
        offset = offset,
        created_by_me = created_by_me
    )
    
@router.get("/meal_plans")
async def get_all_meal_plans(
    request:Request,
    org_id: Annotated[int, Query(title="Organization id")],
    filters: Annotated[_schemas.MealPlanFilterParams, Depends(get_filters)],
        db: _orm.Session = Depends(get_db)):
    try:
        persona = request.state.user.get('user_type')
        meal_plans = _service.get_meal_plans_by_org_id(org_id, db, persona, params=filters)
        return meal_plans
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    

@router.get("/meal_plans/mobile/")
async def get_all_meal_plans_mobile(org_id: Annotated[int, Query(title="Organization id")], 
    request:Request, 
    filters: Annotated[_schemas.MealPlanFilterParams, Depends(get_filters)], db: _orm.Session = Depends(get_db)):
    try:
        user_id = request.state.user.get('id')
        persona = request.state.user.get('user_type')
        meal_plans = _service.get_meal_plans_by_token(org_id, user_id, persona, db, params=filters)
        return meal_plans
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")