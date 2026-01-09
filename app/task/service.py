# app/task/service.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from typing import List, Optional

import app.task.models as _models
import app.user.models as _user_models
import app.task.schema as _schemas

def get_task_or_404(db: Session, task_id: int):
    task = db.query(_models.Task).filter(_models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task

# --- 1. Create Task (Manager -> Assigns Work) ---
def create_task(db: Session, task_in: _schemas.TaskCreate, current_user: _user_models.User):
    try:
        # Validate Assignee
        assignee = db.query(_user_models.User).filter(
            _user_models.User.id == task_in.assignee_id,
            _user_models.User.role == _user_models.UserRole.digital_creator,
            _user_models.User.is_deleted == False
        ).first()
        
        if not assignee:
            raise HTTPException(status_code=400, detail="Invalid Assignee. Must be an active Digital Creator.")

        # Extract Attachments
        task_data = task_in.dict()
        attachments_data = task_data.pop("attachments", [])

        new_task = _models.Task(
            **task_data,
            assigner_id=current_user.id
        )
        db.add(new_task)
        db.flush()

        # Add Reference Files (Instructions)
        for file_data in attachments_data:
            vault_item = _models.ContentVault(
                uploader_id=current_user.id,
                task_id=new_task.id,
                
                file_url=file_data['file_url'],
                thumbnail_url=file_data.get('thumbnail_url'),
                file_size_mb=file_data['file_size_mb'],
                mime_type=file_data['mime_type'],
                duration_seconds=file_data.get('duration_seconds', 0),
                tags=file_data.get('tags', 'Reference'), 
                
                content_type=new_task.req_content_type,
                is_face_visible=new_task.req_face_visible,
                status=_models.ContentStatus.approved # References are always approved
            )
            db.add(vault_item)

        db.commit()
        db.refresh(new_task)
        return new_task

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

# --- 2. Submit Task (Creator -> Uploads Proof) ---
def submit_task_work(db: Session, task_id: int, submission: _schemas.TaskSubmission, current_user: _user_models.User):
    task = get_task_or_404(db, task_id)

    # Validation: Only the Assignee can submit
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the assigned creator can submit work.")

    if task.status == _models.TaskStatus.completed:
        raise HTTPException(status_code=400, detail="Task is already marked as Completed.")

    try:
        # 1. Add Deliverables to Vault
        for file_data in submission.deliverables:
            vault_item = _models.ContentVault(
                uploader_id=current_user.id,
                task_id=task.id,
                
                file_url=file_data.file_url,
                thumbnail_url=file_data.thumbnail_url,
                file_size_mb=file_data.file_size_mb,
                mime_type=file_data.mime_type,
                duration_seconds=file_data.duration_seconds,
                tags=file_data.tags or "Deliverable",
                
                content_type=task.req_content_type,
                is_face_visible=task.req_face_visible,
                status=_models.ContentStatus.pending # Needs Manager Approval
            )
            db.add(vault_item)

        # 2. Update Status -> Review
        task.status = _models.TaskStatus.review
        
        # 3. Add System Log (Chat)
        sys_msg = _models.TaskChat(
            task_id=task.id,
            user_id=current_user.id,
            message="Submitted work for review.",
            is_system_log=True
        )
        db.add(sys_msg)

        # 4. Add Optional Comment
        if submission.comment:
            user_msg = _models.TaskChat(
                task_id=task.id,
                user_id=current_user.id,
                message=submission.comment
            )
            db.add(user_msg)

        db.commit()
        db.refresh(task)
        return task

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")

# --- 3. Get Tasks (Visibility) ---
def get_all_tasks(db: Session, current_user: _user_models.User, status: Optional[str] = None):
    # Eager load attachments so we can separate them in UI
    query = db.query(_models.Task).options(
        joinedload(_models.Task.assigner),
        joinedload(_models.Task.assignee),
        joinedload(_models.Task.attachments)
    )

    if current_user.role == _user_models.UserRole.digital_creator:
        query = query.filter(_models.Task.assignee_id == current_user.id)
    elif current_user.role == _user_models.UserRole.manager:
        query = query.join(_models.Task.assignee).filter(
            _user_models.User.manager_id == current_user.id
        )
    elif current_user.role == _user_models.UserRole.team_member:
        query = query.filter(_models.Task.assigner_id == current_user.id)

    if status:
        query = query.filter(_models.Task.status == status)

    tasks = query.order_by(_models.Task.created_at.desc()).all()
    
    for task in tasks:
        task.chat_count = len(task.chat_messages)
        
    return tasks

# --- 4. Chat & Updates ---
def update_task(db: Session, task_id: int, updates: _schemas.TaskUpdate, current_user: _user_models.User):
    task = get_task_or_404(db, task_id)

    if current_user.role == _user_models.UserRole.digital_creator:
        if updates.title or updates.priority or updates.description:
             raise HTTPException(status_code=403, detail="Creators can only update status.")

    try:
        update_data = updates.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)
        db.commit()
        db.refresh(task)
        return task
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Update failed")

def get_chat_history(db: Session, task_id: int):
    return db.query(_models.TaskChat)\
        .options(joinedload(_models.TaskChat.author))\
        .filter(_models.TaskChat.task_id == task_id)\
        .order_by(_models.TaskChat.created_at.asc())\
        .all()

def send_chat_message(db: Session, task_id: int, message: str, current_user: _user_models.User):
    task = get_task_or_404(db, task_id)
    
    # 1. Check direct involvement
    is_assigner = task.assigner_id == current_user.id
    is_assignee = task.assignee_id == current_user.id
    
    # 2. Check Hierarchy (Manager Oversight)
    # Allows the Creator's Manager to chat even if they didn't create the task themselves
    is_manager = False
    if task.assignee.manager_id == current_user.id: 
        is_manager = True
    
    # 3. Enforce Permissions
    # Admins can always chat. Everyone else must be related to the task.
    if current_user.role != _user_models.UserRole.admin:
        if not (is_assigner or is_assignee or is_manager):
            raise HTTPException(status_code=403, detail="You do not have permission to chat in this task.")

    try:
        chat_msg = _models.TaskChat(
            task_id=task_id, 
            user_id=current_user.id, 
            message=message
        )
        db.add(chat_msg)
        db.commit()
        db.refresh(chat_msg)
        return chat_msg
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to send message.")