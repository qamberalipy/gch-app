from fastapi import APIRouter
from app.MealPlan.meal_plan import router

API_STR = ""

mealplan_router = APIRouter(prefix=API_STR)
mealplan_router.include_router(router)