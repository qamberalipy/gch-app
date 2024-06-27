from fastapi import APIRouter
from app.Leads1.lead import router

API_STR = "/leads"

leads_router = APIRouter(prefix=API_STR)
leads_router.include_router(router)