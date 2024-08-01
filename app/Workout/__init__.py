
from fastapi import APIRouter
from .workout import router



workout_router = APIRouter()
workout_router.include_router(router)
