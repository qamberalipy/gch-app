# app/task/task.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

import app.core.db.session as _database
import app.user.user as _user_auth
import app.user.models as _user_models
import app.task.schema as _schemas
import app.task.service as _services

router = APIRouter()

def get_db():
    db = _database.SessionLocal()
    try: yield db
    finally: db.close()

# --- Utility: Get Assignees ---
@router.get("/assignees", response_model=List[_schemas.UserMinimal], tags=["TASK API"])
def get_available_creators(
    current_user: _user_models.User = Depends(_user_auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns valid models for the logged-in user (Manager or Team Member)
    based on the strict hierarchy rules.
    """
    return _services.get_my_assignees(db, current_user)

# --- Task CRUD ---

@router.get("/", response_model=List[_schemas.TaskOut], tags=["TASK API"])
def list_tasks(
    status: Optional[str] = None,
    current_user: _user_models.User = Depends(_user_auth.get_current_user),
    db: Session = Depends(get_db)
):
    """View tasks based on role visibility permissions."""
    return _services.get_all_tasks(db, current_user, status)

@router.post("/", response_model=_schemas.TaskOut, status_code=status.HTTP_201_CREATED, tags=["TASK API"])
def create_task(
    task_in: _schemas.TaskCreate,
    current_user: _user_models.User = Depends(_user_auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Admin/Manager/Team Member creates task."""
    if current_user.role == _user_models.UserRole.digital_creator:
        raise HTTPException(status_code=403, detail="Creators cannot assign tasks.")
    return _services.create_task(db, task_in, current_user)

@router.get("/{task_id}", response_model=_schemas.TaskOut, tags=["TASK API"])
def get_task(
    task_id: int,
    current_user: _user_models.User = Depends(_user_auth.get_current_user),
    db: Session = Depends(get_db)
):
    return _services.get_task_or_404(db, task_id)

@router.put("/{task_id}", response_model=_schemas.TaskOut, tags=["TASK API"])
def update_task(
    task_id: int,
    updates: _schemas.TaskUpdate,
    current_user: _user_models.User = Depends(_user_auth.get_current_user),
    db: Session = Depends(get_db)
):
    return _services.update_task(db, task_id, updates, current_user)

@router.delete("/{task_id}", status_code=status.HTTP_200_OK, tags=["TASK API"])
def delete_task(
    task_id: int,
    current_user: _user_models.User = Depends(_user_auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete task. Allowed for Admin or the original Assigner."""
    return _services.delete_task(db, task_id, current_user)

# --- WORK SUBMISSION (For Creators) ---

@router.post("/{task_id}/submit", response_model=_schemas.TaskOut, tags=["TASK API"])
def submit_work(
    task_id: int,
    submission: _schemas.TaskSubmission,
    current_user: _user_models.User = Depends(_user_auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creator uploads proof of work (Deliverables).
    - Saves files to ContentVault.
    - Updates Status to 'In Review'.
    """
    return _services.submit_task_work(db, task_id, submission, current_user)

# --- Chat ---

@router.get("/{task_id}/chat", response_model=List[_schemas.ChatMsgOut], tags=["TASK API"])
def get_chat(
    task_id: int,
    current_user: _user_models.User = Depends(_user_auth.get_current_user),
    db: Session = Depends(get_db)
):
    return _services.get_chat_history(db, task_id)

@router.post("/{task_id}/chat", response_model=_schemas.ChatMsgOut, tags=["TASK API"])
def send_chat(
    task_id: int,
    chat_in: _schemas.ChatMsgCreate,
    current_user: _user_models.User = Depends(_user_auth.get_current_user),
    db: Session = Depends(get_db)
):
    return _services.send_chat_message(db, task_id, chat_in.message, current_user)

# app/task/task.py (Add this endpoint)

@router.delete("/content/{content_id}", status_code=status.HTTP_200_OK, tags=["TASK API"])
def remove_attachment(
    content_id: int,
    current_user: _user_models.User = Depends(_user_auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific file attachment (Used for editing submissions)."""
    return _services.delete_content_item(db, content_id, current_user)