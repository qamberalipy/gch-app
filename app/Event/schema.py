import pydantic
import datetime
from datetime import date
from typing import Optional
from enum import Enum

class RecurrencyEnum(str, Enum):
    daily = "daily"
    weekly = "weekly"
    yearly = "yearly"
    monthly = "monthly"

class StatusEnum(str, Enum):
    pending = "pending"
    inprogress = "inprogress"
    completed = "completed"

class EventBase(pydantic.BaseModel):
    activity: str
    description: Optional[str]
    start_time: datetime.datetime
    end_time: datetime.datetime
    org_id: Optional[int]
    coach_id: int
    credit_type: Optional[str]
    recurrency: Optional[RecurrencyEnum]
    participants: Optional[str]
    status: StatusEnum
    link: Optional[str]
    notes: Optional[str]
    updated_at: Optional[datetime.datetime]
    updated_by: Optional[int]

class EventCreate(EventBase):
    created_by: Optional[int]
    created_at: Optional[datetime.datetime]

class EventRead(EventBase):
    id: int
    is_deleted: bool
    class Config:
        from_attributes = True

class EventUpdate(EventBase):
    pass

class EventDelete(EventBase):
    is_deleted: bool
    updated_at: datetime.datetime = datetime.datetime.now()
    updated_by: int
    class Config:
        from_attributes = True
