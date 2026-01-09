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

def get_my_assignees(db: Session, current_user: _user_models.User):
    try:
        """
        Returns the list of Digital Creators that the current user can manage.
        """
        # Base query: Only Active Digital Creators
        query = db.query(_user_models.User).filter(
            _user_models.User.role == _user_models.UserRole.digital_creator,
            _user_models.User.is_deleted == False
        )

        if current_user.role == _user_models.UserRole.manager:
            # Manager sees their own assigned models
            query = query.filter(_user_models.User.manager_id == current_user.id)
        
        elif current_user.role == _user_models.UserRole.team_member:
            # Team Members see creators belonging to their Manager
            if current_user.manager_id:
                query = query.filter(_user_models.User.manager_id == current_user.manager_id)
            else:
                return [] # Unassigned team member sees no one
                
        # Admin sees everyone
        return query.all()
    except SQLAlchemyError as e:
        print(f"Database error in get_my_assignees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in get_my_assignees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# --- 1. Create Task ---
def create_task(db: Session, task_in: _schemas.TaskCreate, current_user: _user_models.User):
    try:
        # Validate Assignee (Must be active and a creator)
        assignee = db.query(_user_models.User).filter(
            _user_models.User.id == task_in.assignee_id,
            _user_models.User.role == _user_models.UserRole.digital_creator,
            _user_models.User.is_deleted == False
        ).first()
        
        if not assignee:
            raise HTTPException(status_code=400, detail="Invalid or Deleted Assignee.")

        # Permission Check: 
        # Ensure the Assignee belongs to the Creator's team (or Manager's team)
        if current_user.role != _user_models.UserRole.admin:
            required_manager_id = current_user.id if current_user.role == _user_models.UserRole.manager else current_user.manager_id
            
            # If team member has no manager, they can't assign
            if current_user.role == _user_models.UserRole.team_member and not required_manager_id:
                 raise HTTPException(status_code=403, detail="You are not linked to a manager.")

            if assignee.manager_id != required_manager_id:
                raise HTTPException(status_code=403, detail="You can only assign tasks to models in your team.")

        # Extract Attachments
        task_data = task_in.dict()
        attachments_data = task_data.pop("attachments", [])

        new_task = _models.Task(
            **task_data,
            assigner_id=current_user.id
        )
        db.add(new_task)
        db.flush()

        # Add Reference Files
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
                status=_models.ContentStatus.approved # References are auto-approved
            )
            db.add(vault_item)

        db.commit()
        db.refresh(new_task)
        return new_task

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

# --- 2. Submit Task ---
def submit_task_work(db: Session, task_id: int, submission: _schemas.TaskSubmission, current_user: _user_models.User):
    task = get_task_or_404(db, task_id)

    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the assigned creator can submit work.")

    try:
        # Add Deliverables
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
                status=_models.ContentStatus.pending
            )
            db.add(vault_item)

        task.status = _models.TaskStatus.review
        
        # Add System Log
        sys_msg = _models.TaskChat(
            task_id=task.id,
            user_id=current_user.id,
            message="Submitted work for review.",
            is_system_log=True
        )
        db.add(sys_msg)

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

# --- 3. Get Tasks ---
def get_all_tasks(db: Session, current_user: _user_models.User, status: Optional[str] = None):
    query = db.query(_models.Task).options(
        joinedload(_models.Task.assigner),
        joinedload(_models.Task.assignee),
        joinedload(_models.Task.attachments)
    )

    # 1. Creator: Sees only their own tasks
    if current_user.role == _user_models.UserRole.digital_creator:
        query = query.filter(_models.Task.assignee_id == current_user.id)
    
    # 2. Manager: Sees tasks for ALL models they manage
    elif current_user.role == _user_models.UserRole.manager:
        query = query.join(_models.Task.assignee).filter(
            _user_models.User.manager_id == current_user.id,
            _user_models.User.is_deleted == False  # Filter out tasks for deleted users
        )

    # 3. Team Member: Sees tasks for ALL models their Manager manages
    elif current_user.role == _user_models.UserRole.team_member:
        if current_user.manager_id:
             query = query.join(_models.Task.assignee).filter(
                _user_models.User.manager_id == current_user.manager_id,
                _user_models.User.is_deleted == False
            )
        else:
             # Unassigned team member sees nothing or only tasks they created (optional)
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
    
    # Permission Logic
    can_chat = False
    if current_user.role == _user_models.UserRole.admin:
        can_chat = True
    elif task.assigner_id == current_user.id or task.assignee_id == current_user.id:
        can_chat = True
    # Allow Manager/Team to chat if they manage the assignee
    elif task.assignee.manager_id == current_user.id:
        can_chat = True
    elif current_user.role == _user_models.UserRole.team_member and task.assignee.manager_id == current_user.manager_id:
        can_chat = True

    if not can_chat:
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