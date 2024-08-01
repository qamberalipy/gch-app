from fastapi import APIRouter
from app.Membership.membership import router

API_STR = "/membership_plan"

membership_router = APIRouter()
membership_router.include_router(router)