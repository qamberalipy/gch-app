# app/task/models.py
from enum import Enum as _PyEnum
import sqlalchemy as _sql
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import app.core.db.session as _database

# --- Enums ---
class TaskStatus(str, _PyEnum):
    todo = "To Do"
    in_progress = "In Progress"
    review = "In Review" # Creator submitted, Manager checking
    blocked = "Blocked"
    completed = "Completed"

class TaskPriority(str, _PyEnum):
    low = "Low"
    medium = "Medium"
    high = "High"

class ContentType(str, _PyEnum):
    ppv = "PPV"
    feed = "Feed"
    promo = "Promo"
    story = "Story"
    other = "Other"

class ContentStatus(str, _PyEnum):
    pending = "Pending Review" 
    approved = "Approved"       
    rejected = "Rejected"       
    archived = "Archived"       

# --- Models ---

class Task(_database.Base):
    __tablename__ = "task"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    
    # Ownership
    assigner_id = _sql.Column(_sql.Integer, _sql.ForeignKey("user.id"), nullable=False) 
    assignee_id = _sql.Column(_sql.Integer, _sql.ForeignKey("user.id"), nullable=False) 
    
    # Core Details
    title = _sql.Column(_sql.String(150), nullable=False)
    description = _sql.Column(_sql.Text, nullable=True)
    status = _sql.Column(_sql.Enum(TaskStatus, name="task_status"), default=TaskStatus.todo, nullable=False)
    priority = _sql.Column(_sql.Enum(TaskPriority, name="task_priority"), default=TaskPriority.medium, nullable=False)
    
    # Deadlines
    due_date = _sql.Column(_sql.DateTime, nullable=True)
    completed_at = _sql.Column(_sql.DateTime, nullable=True)
    
    # Requirements (Context)
    req_content_type = _sql.Column(_sql.Enum(ContentType, name="content_type_enum"), nullable=False)
    req_length = _sql.Column(_sql.String(50), nullable=True)
    req_outfit_tags = _sql.Column(_sql.String(255), nullable=True) 
    req_face_visible = _sql.Column(_sql.Boolean, default=True)
    req_watermark = _sql.Column(_sql.Boolean, default=False)
    context = _sql.Column(_sql.String(100), default="General") 

    # Timestamps
    created_at = _sql.Column(_sql.DateTime(timezone=True), server_default=func.now())
    updated_at = _sql.Column(_sql.DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # [FIX]: Changed back_populates to backref so 'User' model doesn't need changes
    assigner = relationship("User", foreign_keys=[assigner_id], backref="tasks_created")
    assignee = relationship("User", foreign_keys=[assignee_id], backref="tasks_assigned")
    
    # Internal relationships (within this module) can keep back_populates
    chat_messages = relationship("TaskChat", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("ContentVault", back_populates="task") 


class TaskChat(_database.Base):
    __tablename__ = "task_chat"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    task_id = _sql.Column(_sql.Integer, _sql.ForeignKey("task.id"), nullable=False)
    user_id = _sql.Column(_sql.Integer, _sql.ForeignKey("user.id"), nullable=False)
    message = _sql.Column(_sql.Text, nullable=False)
    is_system_log = _sql.Column(_sql.Boolean, default=False) 
    created_at = _sql.Column(_sql.DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="chat_messages")
    # [FIX]: Changed back_populates to backref
    author = relationship("User", backref="task_comments")


class ContentVault(_database.Base):
    """
    Central storage for all files (Reference, Deliverables, Drive).
    """
    __tablename__ = "content_vault"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    
    # Who uploaded it? (Crucial for distinguishing Instructions vs Submission)
    uploader_id = _sql.Column(_sql.Integer, _sql.ForeignKey("user.id"), nullable=False)
    task_id = _sql.Column(_sql.Integer, _sql.ForeignKey("task.id"), nullable=True)

    # File Data
    file_url = _sql.Column(_sql.String(500), nullable=False)
    thumbnail_url = _sql.Column(_sql.String(500), nullable=True)
    file_size_mb = _sql.Column(_sql.Float, nullable=True)
    mime_type = _sql.Column(_sql.String(50), nullable=True) 
    duration_seconds = _sql.Column(_sql.Integer, nullable=True) 

    # Metadata
    content_type = _sql.Column(_sql.Enum(ContentType, name="content_type_enum"), nullable=False)
    tags = _sql.Column(_sql.String(255), nullable=True)
    is_face_visible = _sql.Column(_sql.Boolean, default=True)
    
    status = _sql.Column(_sql.Enum(ContentStatus, name="content_status"), default=ContentStatus.pending)
    
    created_at = _sql.Column(_sql.DateTime(timezone=True), server_default=func.now())
    approved_at = _sql.Column(_sql.DateTime, nullable=True)
    approved_by = _sql.Column(_sql.Integer, _sql.ForeignKey("user.id"), nullable=True)

    # [FIX]: Changed back_populates to backref
    uploader = relationship("User", foreign_keys=[uploader_id], backref="uploads")
    task = relationship("Task", back_populates="attachments")