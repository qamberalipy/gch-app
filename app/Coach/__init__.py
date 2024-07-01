from fastapi import APIRouter
from app.Coach.coach import router

API_STR = "/api/coach"

coach_router = APIRouter(prefix=API_STR)
coach_router.include_router(router)