from fastapi import APIRouter
from app.Business.business import router

API_STR = "/business"

business_router = APIRouter(prefix=API_STR)
business_router.include_router(router)