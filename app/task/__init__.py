from fastapi import APIRouter
from app.user.user import router

API_STR = "/api/tasks"

task_router = APIRouter(prefix=API_STR)
task_router.include_router(router)