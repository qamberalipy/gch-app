from fastapi import APIRouter
from app.Exercise.exercise import router

API_STR = ""

exercise_router = APIRouter(prefix=API_STR)
exercise_router.include_router(router)