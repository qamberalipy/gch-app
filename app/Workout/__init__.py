
from fastapi import APIRouter
from .workout import router

API_STR = "/workout_plans"

workout_router = APIRouter(prefix=API_STR)
workout_router.include_router(router)
