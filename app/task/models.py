from enum import Enum as _PyEnum
import sqlalchemy as _sql
from sqlalchemy.orm import relationship
import app.core.db.session as _database

# --- Enums ---
class TaskStatus(str, _PyEnum):
    todo = "To Do"
    in_progress = "In Progress"
    review = "In Review"
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

    # Core Data
    title = _sql.Column(_sql.String(150), nullable=False)
    description = _sql.Column(_sql.Text, nullable=True)
    status = _sql.Column(_sql.Enum(TaskStatus, name="task_status_enum"), default=TaskStatus.todo, nullable=False)
    priority = _sql.Column(_sql.Enum(TaskPriority, name="task_priority_enum"), default=TaskPriority.medium, nullable=False)
    
    # Deadlines
    due_date = _sql.Column(_sql.DateTime, nullable=True)
    completed_at = _sql.Column(_sql.DateTime, nullable=True)
    
    # Requirements / Context
    req_content_type = _sql.Column(_sql.Enum(ContentType, name="content_type_enum"), nullable=False, default=ContentType.other)
    
    # [UPDATED] Numerical inputs as requested
    req_quantity = _sql.Column(_sql.Integer, default=1, nullable=False) # e.g. 10 Photos
    req_duration_min = _sql.Column(_sql.Integer, nullable=True) # e.g. 15 Minutes
    
    req_outfit_tags = _sql.Column(_sql.String(500), nullable=True) # Comma separated strings
    req_face_visible = _sql.Column(_sql.Boolean, default=True)
    req_watermark = _sql.Column(_sql.Boolean, default=False)
    context = _sql.Column(_sql.String(100), default="General")

    # Timestamps
    created_at = _sql.Column(_sql.DateTime(timezone=True), server_default=_sql.func.now())
    updated_at = _sql.Column(_sql.DateTime(timezone=True), onupdate=_sql.func.now())

    # --- Relationships ---
    # [FIX] We use 'backref' here to inject the property into the User model dynamically
    # This prevents the "User has no property tasks_created" error.
    assigner = relationship("User", foreign_keys=[assigner_id], backref="tasks_created")
    assignee = relationship("User", foreign_keys=[assignee_id], backref="tasks_assigned")
    
    chat_messages = relationship("TaskChat", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("ContentVault", back_populates="task", cascade="all, delete-orphan")


class TaskChat(_database.Base):
    __tablename__ = "task_chat"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    task_id = _sql.Column(_sql.Integer, _sql.ForeignKey("task.id"), nullable=False)
    user_id = _sql.Column(_sql.Integer, _sql.ForeignKey("user.id"), nullable=False)
    message = _sql.Column(_sql.Text, nullable=False)
    is_system_log = _sql.Column(_sql.Boolean, default=False)
    created_at = _sql.Column(_sql.DateTime(timezone=True), server_default=_sql.func.now())

    task = relationship("Task", back_populates="chat_messages")
    author = relationship("User")


class ContentVault(_database.Base):
    __tablename__ = "content_vault"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    uploader_id = _sql.Column(_sql.Integer, _sql.ForeignKey("user.id"), nullable=False)
    task_id = _sql.Column(_sql.Integer, _sql.ForeignKey("task.id"), nullable=True)

    file_url = _sql.Column(_sql.String(500), nullable=False)
    thumbnail_url = _sql.Column(_sql.String(500), nullable=True) # [UPDATED] Now supported
    file_size_mb = _sql.Column(_sql.Float, nullable=True)
    mime_type = _sql.Column(_sql.String(50), nullable=True)
    duration_seconds = _sql.Column(_sql.Integer, nullable=True)

    content_type = _sql.Column(_sql.Enum(ContentType, name="content_type_enum"), nullable=False)
    tags = _sql.Column(_sql.String(255), nullable=True)
    
    status = _sql.Column(_sql.Enum(ContentStatus, name="content_status"), default=ContentStatus.pending)
    created_at = _sql.Column(_sql.DateTime(timezone=True), server_default=_sql.func.now())

    uploader = relationship("User", foreign_keys=[uploader_id])
    task = relationship("Task", back_populates="attachments")