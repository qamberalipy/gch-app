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

# @router.get("/meal_plans/{meal_plan_id}", response_model=_schemas.ReadMealPlan)
# async def get_meal_plan(meal_plan_id: int, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
#     try:
#         if not authorization or not authorization.startswith("Bearer "):
#             raise HTTPException(status_code=401, detail="Invalid or missing access token")

#         _helpers.verify_jwt(authorization, "User")

#         meal_plan = _service.get_meal_plan(meal_plan_id, db)
#         if meal_plan is None:
#             raise HTTPException(status_code=404, detail="Meal plan not found")
#         return meal_plan
#     except IntegrityError as e:
#         logger.error(f"IntegrityError: {e}")
#         raise HTTPException(status_code=400, detail="Integrity error occurred")
#     except DataError as e:
#         logger.error(f"DataError: {e}")
#         raise HTTPException(status_code=400, detail="Data error occurred, check your input")
#     except Exception as e:
#         logger.error(f"Exception: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/meal_plans", response_model=_schemas.ReadMealPlan)
async def create_meal_plan(meal_plan: _schemas.CreateMealPlan, meal: _schemas.CreateMeal ,db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing access token")

        _helpers.verify_jwt(authorization, "User")

        new_meal_plan = _service.create_meal_plan(meal_plan, db)
        new_meal = _service.create_meal(meal, db)
        return new_meal_plan, new_meal
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Integrity error occurred")
    except DataError as e:
        logger.error(f"DataError: {e}")
        raise HTTPException(status_code=400, detail="Data error occurred, check your input")
    except Exception as e:
        logger.error(f"Exception: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# @router.put("/meal_plans", response_model=_schemas.ReadMealPlan)
# async def update_meal_plan(meal_plan: _schemas.UpdateMealPlan, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
#     try:
#         if not authorization or not authorization.startswith("Bearer "):
#             raise HTTPException(status_code=401, detail="Invalid or missing access token")

#         _helpers.verify_jwt(authorization, "User")

#         updated_meal_plan = _service.update_meal_plan(meal_plan, db)
#         if updated_meal_plan is None:
#             raise HTTPException(status_code=404, detail="Meal plan not found")
#         return updated_meal_plan
#     except IntegrityError as e:
#         logger.error(f"IntegrityError: {e}")
#         raise HTTPException(status_code=400, detail="Integrity error occurred")
#     except DataError as e:
#         logger.error(f"DataError: {e}")
#         raise HTTPException(status_code=400, detail="Data error occurred, check your input")
#     except Exception as e:
#         logger.error(f"Exception: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.delete("/meal_plans/{meal_plan_id}", response_model=_schemas.ReadMealPlan)
# async def delete_meal_plan(meal_plan: _schemas.DeleteMeal, db: _orm.Session = Depends(get_db), authorization: str = Header(None)):
#     try:
#         if not authorization or not authorization.startswith("Bearer "):
#             raise HTTPException(status_code=401, detail="Invalid or missing access token")

#         _helpers.verify_jwt(authorization, "User")

#         deleted_meal_plan = _service.delete_meal_plan(meal_plan.id, db)
#         if deleted_meal_plan is None:
#             raise HTTPException(status_code=404, detail="Meal plan not found")
#         return deleted_meal_plan
#     except IntegrityError as e:
#         logger.error(f"IntegrityError: {e}")
#         raise HTTPException(status_code=400, detail="Integrity error occurred")
#     except DataError as e:
#         logger.error(f"DataError: {e}")
#         raise HTTPException(status_code=400, detail="Data error occurred, check your input")
#     except Exception as e:
#         logger.error(f"Exception: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")
