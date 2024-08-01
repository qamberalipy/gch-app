from fastapi import APIRouter
from app.Client.client import router

API_STR = "/member"

client_router = APIRouter()
client_router.include_router(router)