# app/notification/schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeviceTokenCreate(BaseModel):
    token: str
    platform: str = "android"

class NotificationResponse(BaseModel):
    id: int
    title: str
    body: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    click_action_link: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UnreadCount(BaseModel):
    count: int