from fastapi import APIRouter
from app.user.user import router

API_STR = "/users"

user_router = APIRouter(prefix=API_STR)
user_router.include_router(router)