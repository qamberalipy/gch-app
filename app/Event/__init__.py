from fastapi import APIRouter
from app.Event.event import router

API_STR = "/events"

event_router = APIRouter(prefix=API_STR)
event_router.include_router(router)