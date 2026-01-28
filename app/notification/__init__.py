from fastapi import APIRouter
# app/notification/__init__.py
from app.notification.notification import router, ws_router # <--- Import ws_router

API_STR = "/api/notification"

notification_router = APIRouter(prefix=API_STR)
notification_router.include_router(router)

# We will export ws_router separately or include it here if we change how it's mounted in main.py