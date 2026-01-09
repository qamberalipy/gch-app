# app/task/schema.py
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.task.models import TaskStatus, TaskPriority, ContentType, ContentStatus

# --- Helpers ---
class UserMinimal(BaseModel):
    id: int
    full_name: Optional[str] = None
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
    """Used for BOTH creating tasks (Reference) and submitting work (Deliverables)"""
    file_url: str
    file_size_mb: float
    mime_type: str
    thumbnail_url: Optional[str] = None 
    tags: Optional[str] = None
    duration_seconds: Optional[int] = 0

class VaultItemOut(BaseModel):
    id: int
    uploader_id: int  # <--- CRITICAL: Frontend checks this ID to know if it's Instruction or Submission
    file_url: str
    thumbnail_url: Optional[str]
    status: ContentStatus
    duration_seconds: Optional[int]
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
    req_length: Optional[str] = None
    req_outfit_tags: Optional[str] = None
    req_face_visible: bool = True
    req_watermark: bool = False
    context: str = "General"

    # [ATOMIC] Attachments (Reference materials from Manager)
    attachments: List[VaultItemCreate] = []

class TaskSubmission(BaseModel):
    """Payload for Creator when finishing a task"""
    deliverables: List[VaultItemCreate] = Field(..., min_items=1)
    comment: Optional[str] = None 

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime]
    created_at: datetime
    
    req_content_type: ContentType
    req_length: Optional[str]
    req_outfit_tags: Optional[str]
    req_face_visible: bool
    req_watermark: bool
    context: str

    assigner: UserMinimal
    assignee: UserMinimal
    
    chat_count: int = 0 
    attachments: List[VaultItemOut] = []

    class Config:
        orm_mode = True