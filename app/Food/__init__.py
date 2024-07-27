from fastapi import APIRouter
from app.Food.food import router

API_STR = "/food"

food_router = APIRouter(prefix=API_STR)
food_router.include_router(router)