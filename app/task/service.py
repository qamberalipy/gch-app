# app/task/service.py
import datetime
import asyncio
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload, aliased
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status, BackgroundTasks
from typing import List, Optional, Any

import app.task.models as _models
import app.user.models as _user_models
import app.task.schema as _schemas
import app.core.db.session as _database 

# --- Notification Import ---
from app.notification.service import send_smart_notification

# ==========================================
#   NOTIFICATION SAFETY HELPERS
# ==========================================

class ImmediateBackgroundTasks(BackgroundTasks):
    """
    Custom handler to execute FCM tasks immediately 
    since we are already inside a background thread.
    """
    def add_task(self, func: Any, *args: Any, **kwargs: Any) -> None:
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(f"FCM Immediate Execution Failed: {e}")

def _run_async_notification(recipient_ids: List[int], title: str, body: str, entity_id: int, actor_id: int):
    """
    Safe wrapper: Creates its own DB session and Event Loop.
    Wraps everything in try/except to protect the main app.
    """
    # 1. Create a fresh DB session (Essential for background threads)
    new_db = _database.SessionLocal()
    try:
        # 2. Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 3. Run the async 'send_smart_notification'
        # We use ImmediateBackgroundTasks to force FCM to send NOW.
        loop.run_until_complete(
            send_smart_notification(
                db=new_db,
                recipient_ids=recipient_ids,
                title=title,
                body=body,
                background_tasks=ImmediateBackgroundTasks(), # <--- THE FIX
                entity_type="task",
                entity_id=entity_id,
                click_url=f"/task_assigner", 
                actor_id=actor_id
            )
        )
        loop.close()
    except Exception as e:
        # Log error but DO NOT crash the application
        print(f"Background Notification Failed: {e}")
    finally:
        new_db.close()

def _trigger_notification(
    bt: BackgroundTasks, 
    recipients: List[int], 
    title: str, 
    body: str, 
    task_id: int, 
    actor_id: int
):
    """
    Schedules the safe wrapper.
    """
    unique_ids = list(set(recipients))
    if not unique_ids:
        return

    # Add the safe wrapper to FastAPI's background queue
    bt.add_task(
        _run_async_notification,
        unique_ids,
        title,
        body,
        task_id,
        actor_id
    )

# ==========================================
#   CORE SERVICE FUNCTIONS
# ==========================================

def get_task_or_404(db: Session, task_id: int):
    task = db.query(_models.Task).options(
        joinedload(_models.Task.assigner),
        joinedload(_models.Task.assignee),
        joinedload(_models.Task.attachments)
    ).filter(_models.Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task

def get_my_assignees(db: Session, current_user: _user_models.User):
    try:
        query = db.query(_user_models.User).filter(
            _user_models.User.role == _user_models.UserRole.digital_creator,
            _user_models.User.is_deleted == False
        )
        if current_user.role == _user_models.UserRole.manager:
            query = query.filter(_user_models.User.manager_id == current_user.id)
        elif current_user.role == _user_models.UserRole.team_member:
            if current_user.assigned_model_id:
                query = query.filter(_user_models.User.id == current_user.assigned_model_id)
            else:
                return []
        return query.all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

# --- 1. Create Task ---
def create_task(
    db: Session, 
    task_in: _schemas.TaskCreate, 
    current_user: _user_models.User,
    background_tasks: BackgroundTasks 
):
    # [Validation Logic]
    try:
        assignee = db.query(_user_models.User).filter(
            _user_models.User.id == task_in.assignee_id,
            _user_models.User.role == _user_models.UserRole.digital_creator,
            _user_models.User.is_deleted == False
        ).first()
        
        if not assignee:
            raise HTTPException(status_code=400, detail="Invalid or Deleted Assignee.")

        if current_user.role != _user_models.UserRole.admin:
            if current_user.role == _user_models.UserRole.team_member:
                if current_user.assigned_model_id != assignee.id:
                    raise HTTPException(status_code=403, detail="You can only assign tasks to your paired Digital Creator.")
            elif current_user.role == _user_models.UserRole.manager:
                if assignee.manager_id != current_user.id:
                    raise HTTPException(status_code=403, detail="You can only assign tasks to models in your team.")

        # [Data Preparation]
        data = task_in.dict()
        attachments_data = data.pop("attachments", [])
        tags_list = data.pop("req_outfit_tags", [])
        tags_csv = ",".join(tags_list) if tags_list else None

        new_task = _models.Task(
            **data,
            req_outfit_tags=tags_csv,
            assigner_id=current_user.id
        )
        new_task.status = task_in.status.value
        new_task.priority = task_in.priority.value
        new_task.req_content_type = task_in.req_content_type.value

        db.add(new_task)
        db.flush() 

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
                status=_models.ContentStatus.approved.value
            )
            db.add(vault_item)

        db.commit()
        db.refresh(new_task)

        # [SAFE NOTIFICATION BLOCK]
        try:
            recipient_ids = set()
            recipient_ids.add(new_task.assignee_id)

            admin_ids = [u.id for u in db.query(_user_models.User).filter(
                _user_models.User.role == _user_models.UserRole.admin, 
                _user_models.User.is_deleted == False
            ).all()]

            if current_user.role == _user_models.UserRole.manager:
                recipient_ids.add(current_user.id)
                recipient_ids.update(admin_ids)
            elif current_user.role == _user_models.UserRole.team_member:
                if current_user.manager_id:
                    recipient_ids.add(current_user.manager_id)
                recipient_ids.update(admin_ids)
            elif current_user.role == _user_models.UserRole.admin:
                recipient_ids.add(current_user.id)

            _trigger_notification(
                background_tasks,
                list(recipient_ids),
                "New Task Assigned",
                f"{current_user.full_name} assigned a new task: {new_task.title}",
                new_task.id,
                current_user.id
            )
        except Exception as e:
            # Silently fail notification, but TASK IS SUCCESSFUL
            print(f"Notification Error (Ignored): {e}")

        return new_task

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

# --- 2. Update Task ---
def update_task(
    db: Session, 
    task_id: int, 
    updates: _schemas.TaskUpdate, 
    current_user: _user_models.User,
    background_tasks: BackgroundTasks
):
    task = get_task_or_404(db, task_id)

    if current_user.role == _user_models.UserRole.digital_creator:
        allowed_fields = ['status']
        for field in updates.dict(exclude_unset=True).keys():
            if field not in allowed_fields:
                raise HTTPException(status_code=403, detail="Creators can only update task status.")

    try:
        update_data = updates.dict(exclude_unset=True)
        
        old_status = task.status
        new_status = None
        if 'status' in update_data:
            val = update_data['status']
            new_status = val.value if hasattr(val, 'value') else val

        if 'req_outfit_tags' in update_data:
            tags_list = update_data.pop('req_outfit_tags')
            task.req_outfit_tags = ",".join(tags_list) if tags_list else None

        for key, value in update_data.items():
            if hasattr(value, 'value'):
                value = value.value
            setattr(task, key, value)
            
        db.commit()
        db.refresh(task)

        # [SAFE NOTIFICATION BLOCK]
        if new_status and new_status != old_status:
            try:
                recipients = []
                title = "Task Updated"
                body = f"Task '{task.title}' status changed to {new_status}"

                if current_user.id == task.assignee_id:
                    recipients.append(task.assigner_id)
                    body = f"{current_user.full_name} updated status to {new_status}"
                elif current_user.id == task.assigner_id:
                    recipients.append(task.assignee_id)
                elif current_user.role == _user_models.UserRole.admin:
                    recipients.append(task.assignee_id)
                    if task.assigner_id != current_user.id:
                        recipients.append(task.assigner_id)

                if recipients:
                    _trigger_notification(
                        background_tasks, recipients, title, body, task.id, current_user.id
                    )
            except Exception as e:
                print(f"Notification Error (Ignored): {e}")

        return task
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

# --- 3. Delete Task ---
def delete_task(
    db: Session, 
    task_id: int, 
    current_user: _user_models.User,
    background_tasks: BackgroundTasks
):
    task = get_task_or_404(db, task_id)
    
    can_delete = False
    if current_user.role == _user_models.UserRole.admin:
        can_delete = True
    elif task.assigner_id == current_user.id:
        can_delete = True
        
    if not can_delete:
        raise HTTPException(status_code=403, detail="You can only delete tasks you created.")

    # Capture data before deletion
    assignee_id = task.assignee_id
    task_title = task.title

    try:
        db.delete(task)
        db.commit()

        # [SAFE NOTIFICATION BLOCK]
        try:
            if assignee_id != current_user.id:
                _trigger_notification(
                    background_tasks,
                    [assignee_id],
                    "Task Cancelled",
                    f"Task '{task_title}' was removed by {current_user.full_name}",
                    0, 
                    current_user.id
                )
        except Exception as e:
            print(f"Notification Error (Ignored): {e}")

        return {"message": "Task deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

# --- 4. Submit Task ---
def submit_task_work(
    db: Session, 
    task_id: int, 
    submission: _schemas.TaskSubmission, 
    current_user: _user_models.User,
    background_tasks: BackgroundTasks
):
    task = get_task_or_404(db, task_id)

    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the assigned creator can submit work.")

    try:
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
                status=_models.ContentStatus.pending.value
            )
            db.add(vault_item)

        task.status = _models.TaskStatus.completed.value
        task.completed_at = datetime.datetime.now()
        
        sys_msg = _models.TaskChat(
            task_id=task.id,
            user_id=current_user.id,
            message="Work submitted. Task marked as Completed.",
            is_system_log=True
        )
        db.add(sys_msg)
        db.commit()
        db.refresh(task)

        # [SAFE NOTIFICATION BLOCK]
        try:
            _trigger_notification(
                background_tasks,
                [task.assigner_id],
                "Task Submitted",
                f"{current_user.full_name} submitted work for '{task.title}'",
                task.id,
                current_user.id
            )
        except Exception as e:
            print(f"Notification Error (Ignored): {e}")

        return task

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")

# --- 5. Get All Tasks (No Changes needed) ---
def get_all_tasks(
    db: Session, 
    current_user: _user_models.User, 
    skip: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    status: Optional[str] = None,
    assignee_id: Optional[int] = None
):
    try:
        query = db.query(_models.Task).options(
            joinedload(_models.Task.assigner),
            joinedload(_models.Task.assignee),
            joinedload(_models.Task.chat_messages),
            joinedload(_models.Task.attachments)
        )

        if current_user.role == _user_models.UserRole.digital_creator:
            query = query.filter(_models.Task.assignee_id == current_user.id)
        elif current_user.role == _user_models.UserRole.manager:
            AssigneeUser = aliased(_user_models.User)
            query = query.join(AssigneeUser, _models.Task.assignee).filter(
                AssigneeUser.manager_id == current_user.id,
                AssigneeUser.is_deleted == False
            )
        elif current_user.role == _user_models.UserRole.team_member:
            if current_user.assigned_model_id:
                query = query.filter(_models.Task.assignee_id == current_user.assigned_model_id)
            else:
                return {"total": 0, "skip": skip, "limit": limit, "tasks": []}

        if status:
            query = query.filter(_models.Task.status == status)

        if assignee_id:
            query = query.filter(_models.Task.assignee_id == assignee_id)

        if search:
            search_term = f"%{search}%"
            query = query.join(_models.Task.assigner).filter(
                or_(
                    _models.Task.title.ilike(search_term),
                    _user_models.User.full_name.ilike(search_term),
                    _user_models.User.username.ilike(search_term)
                )
            )

        total_records = query.count()
        offset = (skip - 1) * limit
        
        tasks = query.order_by(desc(_models.Task.created_at))\
                    .offset(offset)\
                    .limit(limit)\
                    .all()

        for task in tasks:
            task.chat_count = len(task.chat_messages)
            task.attachments_count = len(task.attachments)
            task.is_created_by_me = (task.assigner_id == current_user.id)

        return {
            "total": total_records,
            "skip": skip,
            "limit": limit,
            "tasks": tasks
        }
    except SQLAlchemyError as e:
        print(f"Database error in get_all_tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

# --- 6. Chat & Content (No Changes needed) ---
def get_chat_history(db: Session, task_id: int, direction: int = 0, last_message_id: int = 0, limit: int = 10):
    query = db.query(_models.TaskChat)\
        .options(joinedload(_models.TaskChat.author))\
        .filter(_models.TaskChat.task_id == task_id)

    if direction == 1 and last_message_id > 0:
        query = query.filter(_models.TaskChat.id < last_message_id)\
                     .order_by(_models.TaskChat.id.desc())
    elif direction == 2 and last_message_id > 0:
        query = query.filter(_models.TaskChat.id > last_message_id)\
                     .order_by(_models.TaskChat.id.asc())
    else:
        query = query.order_by(_models.TaskChat.id.desc())

    messages = query.limit(limit).all()
    if direction != 2:
        messages.reverse()
    return messages

def send_chat_message(db: Session, task_id: int, message: str, current_user: _user_models.User):
    task = get_task_or_404(db, task_id)
    
    can_chat = False
    if current_user.role == _user_models.UserRole.admin:
        can_chat = True
    elif task.assigner_id == current_user.id or task.assignee_id == current_user.id:
        can_chat = True
    elif task.assignee.manager_id == current_user.id:
        can_chat = True
    elif current_user.role == _user_models.UserRole.team_member and task.assignee.id == current_user.assigned_model_id:
        can_chat = True

    if not can_chat:
        raise HTTPException(status_code=403, detail="You do not have permission to chat in this task.")

    try:
        chat_msg = _models.TaskChat(task_id=task_id, user_id=current_user.id, message=message)
        db.add(chat_msg)
        db.commit()
        db.refresh(chat_msg)
        return chat_msg
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to send message.")

def delete_content_item(db: Session, content_id: int, current_user: _user_models.User):
    item = db.query(_models.ContentVault).filter(_models.ContentVault.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    if item.uploader_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only remove files you uploaded.")
    if item.task and item.task.status == _models.TaskStatus.completed.value:
         raise HTTPException(status_code=400, detail="Cannot edit submission for a completed task.")
    try:
        db.delete(item)
        db.commit()
        return {"message": "File removed"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")