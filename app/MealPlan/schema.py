from pydantic import BaseModel, field_validator
import datetime
from typing import Optional, List
from app.MealPlan.models import VisibleForEnum, MealTimeEnum


class MealBase(BaseModel):
    meal_time: str
    food_id: Optional[int] = None
    quantity: Optional[float] = None
    
class CreateMeal(MealBase):
    pass

class ReadMeal(MealBase):
    id: int

class UpdateMeal(MealBase):
    id: int
    updated_by: Optional[int] = None
    updated_at: Optional[datetime.datetime] = None

class DeleteMeal(MealBase):
    is_deleted: bool

class MealPlanBase(BaseModel):
    name: str
    org_id : int
    profile_img: Optional[str]
    visible_for: VisibleForEnum
    description: Optional[str]
    
class CreateMealPlan(MealPlanBase):
    meals: List[CreateMeal]
    member_ids: List[int]
    created_at: Optional[datetime.datetime] = datetime.datetime.now()
    carbs: float
    protein: float
    fats: float
    
    class Config:
        from_attributes = True

class ReadMealPlan(MealPlanBase):
    id: int
    carbs : float
    protein: float
    fats : float
    persona : str

class UpdateMealPlan(BaseModel):
    id: int
    org_id : int
    name: Optional[str] = None
    profile_img: Optional[str] = None
    visible_for: Optional[VisibleForEnum] = None
    description: Optional[str] = None
    carbs : Optional[float] = None
    protein : Optional[float] = None
    fats : Optional[float] = None
    meals: Optional[List[CreateMeal]] = []
    member_id : Optional[List[int]] = []
    updated_by: Optional[int] = None
    updated_at: Optional[datetime.datetime] = None

class DeleteMealPlan(BaseModel):
    id: int

class MealPlanFilterParams(BaseModel):
    visible_for : Optional[VisibleForEnum] = None
    meal_time : Optional[str] = None
    assign_to : Optional[str] = None
    carbs : Optional[str] = None
    protein: Optional[str] = None
    fats : Optional[str] = None
    search_key: Optional[str] = None
    sort_key:Optional[str] = None
    sort_order: Optional[str] = None
    member_id : Optional[List[int]] = []
    food_id : Optional[List[int]] = []
    status: Optional[str] = None
    limit:Optional[int] = None
    offset:Optional[int] = None
    created_by_me : Optional[int] = None
    
    @field_validator('visible_for', mode='before')
    def map_visible_for(cls, value):
        if value == 'Only myself':
            return VisibleForEnum.only_myself
        elif value == 'Staff of my gym':
            return VisibleForEnum.staff
        elif value == 'Members of my gym':
            return VisibleForEnum.members
        elif value == 'Everyone in my gym':
            return VisibleForEnum.everyone
        return value
    
class ShowMealPlan(BaseModel):
    meal_plan_id: int
    org_id : int
    name: Optional[str] = None
    profile_img: Optional[str] = None
    visible_for: Optional[VisibleForEnum] = None
    description: Optional[str] = None
    meals: Optional[List[CreateMeal]] = []
    member_id : Optional[List[int]] = []
    carbs : Optional[float] = None
    protein : Optional[float] = None
    fats : Optional[float] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime.datetime] = None
    updated_by: Optional[int] = None
    updated_at: Optional[datetime.datetime] = None
        
class MemberMealPlanBase(BaseModel):
    id: int
    member_id : int
    meal_plan_id : int

class CreateMemberMealPlan(BaseModel):
    id: int
    member_id : int
    meal_plan_id : int
    
class DeleteMemberMealPlan(MemberMealPlanBase):
    is_deleted : bool 

class UpdateMemberMealPlan(MemberMealPlanBase):
    pass

class UpdateMemberMealPlan(BaseModel):
    id: int
    member_id : Optional[int] = None
    meal_plan_id : Optional[int] = None
    
