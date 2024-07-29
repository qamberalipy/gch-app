import pydantic
import datetime
from datetime import date
from app.MealPlan.models import VisibleForEnum, MealTimeEnum
from typing import Optional

class MealPlanBase(pydantic.BaseModel):
    name: str
    profile_img : Optional[str]
    visible_for : VisibleForEnum
    description : Optional[str]
    
    class Config:
        orm_mode = True
    
class CreateMealPlan(MealPlanBase):
    created_by : Optional[int] = None
    created_at : Optional[datetime.datetime] = datetime.datetime.now()

class ReadMealPlan(MealPlanBase):
    id : int
    
class UpdateMealPlan(MealPlanBase):
    id : int
    updated_by : Optional[int] = None
    updated_at : Optional[datetime.datetime] = None

class DeleteMealPlan(MealPlanBase):
    is_deleted: bool    
   
   
   
     
class MealBase(pydantic.BaseModel):
    meal_time : MealTimeEnum
    meal_plan_id : int 
    food_id : int
    quantity : float
    
class CreateMeal(MealBase):
    created_by : Optional[int] = None
    created_at : Optional[datetime.datetime] = datetime.datetime.now()
    
class ReadMeal(MealBase):
    id : int
    
class UpdateMeal(MealBase):
    id : int
    updated_by : Optional[int] = None
    updated_at : Optional[datetime.datetime] = None
    
class DeleteMeal(MealBase):
    is_deleted: bool