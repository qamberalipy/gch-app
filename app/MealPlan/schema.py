from pydantic import BaseModel, field_validator
import datetime
from typing import Optional, List
from app.MealPlan.models import VisibleForEnum, MealTimeEnum


class MealBase(BaseModel):
    meal_time: Optional[MealTimeEnum] = None
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

    class Config:
        from_attributes = True

class ReadMealPlan(MealPlanBase):
    id: int

class UpdateMealPlan(BaseModel):
    id: int
    org_id : int
    name: Optional[str] = None
    profile_img: Optional[str] = None
    visible_for: Optional[VisibleForEnum] = None
    description: Optional[str] = None
    meals: Optional[List[CreateMeal]] = []
    member_id : Optional[List[int]] = []
    updated_by: Optional[int] = None
    updated_at: Optional[datetime.datetime] = None

class DeleteMealPlan(BaseModel):
    id: int

class MealPlanFilterParams(BaseModel):
    visible_for : Optional[VisibleForEnum] = None
    assign_to : Optional[str] = None
    food_nutrients : Optional[str] = None
    search_key: Optional[str] = None
    sort_order: Optional[str] = None
    status: Optional[str] = None
    limit:Optional[int] = None
    offset:Optional[int] = None
    
    @field_validator('visible_for', mode='before')
    def map_visible_for(cls, value):
        if value == 'only_myself':
            return VisibleForEnum.only_myself
        elif value == 'staff_of_my_gym':
            return VisibleForEnum.staff
        elif value == 'members_of_my_gym':
            return VisibleForEnum.members
        elif value == 'everyone_in_my_gym':
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
    
