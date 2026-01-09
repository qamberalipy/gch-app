from typing import Optional, List, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.task.models import TaskStatus, TaskPriority, ContentType, ContentStatus

# --- Helpers ---
class UserMinimal(BaseModel):
    id: int
    full_name: Optional[str] = None
    username: Optional[str] = None
    profile_picture_url: Optional[str] = None
    role: str
    class Config:
        orm_mode = True

# --- Chat ---
class ChatMsgCreate(BaseModel):
    message: str = Field(..., min_length=1)

class ChatMsgOut(BaseModel):
    id: int
    message: str
    is_system_log: bool
    created_at: datetime
    author: UserMinimal
    class Config:
        orm_mode = True

# --- Vault / Attachments ---
class VaultItemCreate(BaseModel):
    file_url: str
    file_size_mb: float
    mime_type: str
    thumbnail_url: Optional[str] = None 
    tags: Optional[str] = None
    duration_seconds: Optional[int] = 0

class VaultItemOut(BaseModel):
    id: int
    uploader_id: int
    file_url: str
    thumbnail_url: Optional[str]
    status: ContentStatus
    created_at: datetime
    class Config:
        orm_mode = True

# --- Task Actions ---
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: Optional[str] = None
    assignee_id: int
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_date: Optional[datetime] = None
    
    # Specs
    req_content_type: ContentType
    req_quantity: int = 1
    req_duration_min: Optional[int] = 0
    req_outfit_tags: Optional[List[str]] = [] # Frontend sends array, we convert to CSV
    req_face_visible: bool = True
    req_watermark: bool = False
    context: str = "General"

    attachments: List[VaultItemCreate] = []

    @validator('req_outfit_tags', pre=True)
    def parse_tags(cls, v):
        if isinstance(v, str):
            return v.split(',')
        return v

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    
    # Specs updates
    req_quantity: Optional[int] = None
    req_duration_min: Optional[int] = None
    req_outfit_tags: Optional[List[str]] = None

class TaskSubmission(BaseModel):
    deliverables: List[VaultItemCreate] = Field(..., min_items=1)
    comment: Optional[str] = None 

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime]
    created_at: datetime
    
    req_content_type: ContentType
    req_quantity: int
    req_duration_min: Optional[int]
    req_outfit_tags: Optional[str] # Returns as CSV string
    req_face_visible: bool
    req_watermark: bool
    context: str

    assigner: UserMinimal
    assignee: UserMinimal
    
    chat_count: int = 0 
    attachments: List[VaultItemOut] = []

    class Config:
        orm_mode = True