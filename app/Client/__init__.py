from fastapi import APIRouter
from app.Client.client import router

API_STR = "/api/client"

client_router = APIRouter(prefix=API_STR)
client_router.include_router(router)