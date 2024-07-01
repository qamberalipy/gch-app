from fastapi import APIRouter
from app.Membership.membership import router

API_STR = "/api/membership"

membership_router = APIRouter(prefix=API_STR)
membership_router.include_router(router)