from typing import List
from fastapi import FastAPI, Header,APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError, DataError
import app.MealPlan.schema as _schemas
import sqlalchemy.orm as _orm
import app.MealPlan.service as _service
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


@router.post("/meal_plans", response_model=_schemas.ReadMealPlan)
async def create_meal_plan(meal_plan: _schemas.CreateMealPlan, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")

        new_meal_plan = _service.create_meal_plan(meal_plan, db)

        _service.create_meal(new_meal_plan.id,meal_plan.meals, db)

        return new_meal_plan
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
   

@router.get("/meal_plans", response_model=_schemas.ShowMealPlan)
async def get_meal_plans(id:int , db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        meal_plans = _service.get_meal_plan_by_id(id,db)    
        return meal_plans
    
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")


@router.put("/meal_plans", response_model=_schemas.ReadMealPlan)
async def update_meal_plan(meal_plan: _schemas.UpdateMealPlan, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")

        updated_meal_plan = _service.update_meal_plan(meal_plan.id, meal_plan, db)

        return updated_meal_plan
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
   


@router.delete("/meal_plans", response_model=_schemas.ReadMealPlan)
async def delete_meal_plan(meal_plan: _schemas.DeleteMealPlan, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")

        deleted_meal_plan = _service.delete_meal_plan(meal_plan.id, db)
        if deleted_meal_plan is None:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        return deleted_meal_plan
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
       
    
@router.get("/meal_plans/getAll", response_model=List[_schemas.ShowMealPlan])
async def get_all_meal_plans(org_id: int, request:Request,db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")
        
        params = {
            "org_id": org_id,
            "search_key": request.query_params.get("search_key"),
            "visible_for" : request.query_params.get("visible_for"),
            "assign_to" : request.query_params.get("assign_to"),
            "sort_order": request.query_params.get("sort_order"),
            "status": request.query_params.get("status"),
            "limit":request.query_params.get('limit') ,
            "offset":request.query_params.get('offset')
        }
        print(params)

        meal_plans = _service.get_meal_plans_by_org_id(org_id,db,params=_schemas.MealPlanFilterParams(**params))
        return meal_plans
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
   