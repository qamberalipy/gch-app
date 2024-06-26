
import pydantic
import datetime
from datetime import date
from typing import Optional


class CoachBase(pydantic.BaseModel):
    coach_name: str

class CoachCreate(CoachBase):
    org_id: int

class CoachRead(CoachBase):
    id: int
    is_deleted: bool

    class Config:
        from_attributes = True
        