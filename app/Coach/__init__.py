from fastapi import APIRouter
from app.Coach.coach import router

API_STR = "/coach"

coach_router = APIRouter()
coach_router.include_router(router)