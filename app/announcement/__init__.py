from fastapi import APIRouter
from app.announcement.announcement import router

API_STR = "/api/announcement"

announcement_router = APIRouter(prefix=API_STR)
announcement_router.include_router(router)