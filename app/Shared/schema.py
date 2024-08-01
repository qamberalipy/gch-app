import pydantic
import datetime
from datetime import date
from typing import Optional, List, Any

class User(pydantic.BaseModel):
    first_name: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    user_type: str

