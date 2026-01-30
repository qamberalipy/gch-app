# app/notification/service.py
from sqlalchemy.orm import Session
from fastapi import WebSocket, BackgroundTasks
from typing import List, Dict
import asyncio
from firebase_admin import messaging

from app.notification import models, schema
from app.user.models import User
import app.core.db.session as _database

# --- A. WebSocket Manager ---
class NotificationManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def broadcast_personal(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id][:]:
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(connection, user_id)

ws_manager = NotificationManager()

# --- B. Background FCM Worker ---
def _send_fcm_background(tokens: List[str], title: str, body: str, data: dict):
    if not tokens: return
    batch_limit = 500
    for i in range(0, len(tokens), batch_limit):
        chunk = tokens[i : i + batch_limit]
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=data,
            tokens=chunk
        )
        try:
            messaging.send_multicast(message)
        except Exception as e:
            print(f"FCM Background Error: {e}")

# --- C. Core CRUD Logic ---

def register_device_token(db: Session, user: User, payload: schema.DeviceTokenCreate):
    existing = db.query(models.UserDevice).filter(models.UserDevice.fcm_token == payload.token).first()
    if existing:
        existing.user_id = user.id
        existing.platform = payload.platform
    else:
        new_device = models.UserDevice(user_id=user.id, fcm_token=payload.token, platform=payload.platform)
        db.add(new_device)
    db.commit()
    return {"message": "Device registered successfully"}

def get_my_notifications(
    db: Session, 
    user: User, 
    filter_type: str = "all",
    limit: int = 20, 
    skip: int = 0
):
    query = db.query(models.Notification).filter(models.Notification.recipient_id == user.id)
    
    if filter_type == "unread":
        query = query.filter(models.Notification.is_read == False)
    
    query = query.order_by(models.Notification.is_read.asc(), models.Notification.created_at.desc())
    
    notifications = query.offset(skip).limit(limit).all()
    
    unread_count = db.query(models.Notification).filter(
        models.Notification.recipient_id == user.id, 
        models.Notification.is_read == False
    ).count()

    return {
        "total_unread": unread_count,
        "items": notifications,
        "next_cursor": None 
    }

def count_unread(db: Session, user: User):
    count = db.query(models.Notification)\
              .filter(models.Notification.recipient_id == user.id, models.Notification.is_read == False)\
              .count()
    return {"count": count}

def mark_as_read(db: Session, user: User, notification_id: int):
    notif = db.query(models.Notification).filter(
        models.Notification.id == notification_id, 
        models.Notification.recipient_id == user.id
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
        return {"status": "success"}
    return {"status": "not_found"}

def mark_all_as_read(db: Session, user: User):
    db.query(models.Notification)\
      .filter(models.Notification.recipient_id == user.id, models.Notification.is_read == False)\
      .update({models.Notification.is_read: True}, synchronize_session=False)
    db.commit()
    return {"status": "success"}

# --- D. Unified Sender ---

async def send_smart_notification(
    db: Session,
    recipient_ids: List[int],
    title: str,
    body: str,
    background_tasks: BackgroundTasks,
    category: models.NotificationCategory,
    severity: models.NotificationSeverity,
    entity_type: str = "general",
    entity_id: int = None,
    click_url: str = "/",
    actor_id: int = None
):
    valid_ids = list(set(recipient_ids))
    if not valid_ids: return

    # 1. Bulk DB Insert
    new_notifs = []
    for uid in valid_ids:
        new_notifs.append(models.Notification(
            recipient_id=uid,
            actor_id=actor_id,
            title=title,
            body=body,
            category=category.value,
            severity=severity.value,
            entity_type=entity_type,
            entity_id=entity_id,
            click_action_link=click_url
        ))
    db.add_all(new_notifs)
    db.commit() 
    
    # 2. WebSocket Broadcast
    ws_payload = {
        "title": title,
        "body": body,
        "category": category.value,
        "severity": severity.value,
        "link": click_url,
        "entity_id": str(entity_id)
    }
    for uid in valid_ids:
        await ws_manager.broadcast_personal({"type": "new_notification", "data": ws_payload}, uid)

    # 3. Mobile Push (Only High/Critical)
    if severity in [models.NotificationSeverity.HIGH, models.NotificationSeverity.CRITICAL]:
        devices = db.query(models.UserDevice).filter(models.UserDevice.user_id.in_(valid_ids)).all()
        if devices:
            tokens = [d.fcm_token for d in devices]
            fcm_data = {
                "click_action": "FLUTTER_NOTIFICATION_CLICK",
                "route": click_url,
                "category": category.value,
                "entity_id": str(entity_id) if entity_id else ""
            }
            background_tasks.add_task(_send_fcm_background, tokens, title, body, fcm_data)

    return True

# --- E. PUBLIC HELPER (The "Clean" Wrapper) ---

def _background_notification_wrapper(
    recipient_ids: List[int], 
    title: str, 
    body: str, 
    category: models.NotificationCategory, 
    severity: models.NotificationSeverity, 
    entity_id: int, 
    click_url: str,
    actor_id: int
):
    """
    Independent wrapper that manages its own DB session.
    """
    db = _database.SessionLocal()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(
            send_smart_notification(
                db=db,
                recipient_ids=recipient_ids,
                title=title,
                body=body,
                background_tasks=BackgroundTasks(), # Dummy BT
                category=category,
                severity=severity,
                entity_type=category.value,
                entity_id=entity_id,
                click_url=click_url,
                actor_id=actor_id
            )
        )
        loop.close()
    except Exception as e:
        print(f"Background Notification Failed: {e}")
    finally:
        db.close()

def notify_users(
    background_tasks: BackgroundTasks,
    recipient_ids: List[int],
    title: str,
    body: str,
    category: models.NotificationCategory,
    severity: models.NotificationSeverity,
    entity_id: int = None,
    click_url: str = "/",
    actor_id: int = None
):
    """
    Call this function from ANY module (Task, Invoice, etc.) to send notifications.
    """
    background_tasks.add_task(
        _background_notification_wrapper,
        recipient_ids, title, body, category, severity, entity_id, click_url, actor_id
    )