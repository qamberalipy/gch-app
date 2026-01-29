# app/notification/service.py
from sqlalchemy.orm import Session
from fastapi import WebSocket, BackgroundTasks, HTTPException
from typing import List, Dict, Optional
import firebase_admin
from firebase_admin import messaging

from app.notification import models, schema
from app.user.models import User

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
        """Send message to a specific user's active sockets"""
        if user_id in self.active_connections:
            # Iterate over copy to allow safe removal
            for connection in self.active_connections[user_id][:]:
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(connection, user_id)

ws_manager = NotificationManager()

# --- B. Background FCM Worker ---
def _send_fcm_background(tokens: List[str], title: str, body: str, data: dict):
    if not tokens:
        return
    
    # Chunk tokens if > 500 (Firebase limit)
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

# --- C. Core Logic Functions ---

def register_device_token(db: Session, user: User, payload: schema.DeviceTokenCreate):
    """Saves or updates the FCM token for a user."""
    existing = db.query(models.UserDevice).filter(
        models.UserDevice.fcm_token == payload.token
    ).first()
    
    if existing:
        existing.user_id = user.id
        existing.platform = payload.platform
    else:
        new_device = models.UserDevice(
            user_id=user.id, 
            fcm_token=payload.token, 
            platform=payload.platform
        )
        db.add(new_device)
    
    db.commit()
    return {"message": "Device registered successfully"}

def get_my_notifications(db: Session, user: User, limit: int = 20):
    """Fetches notification history."""
    return db.query(models.Notification)\
             .filter(models.Notification.recipient_id == user.id)\
             .order_by(models.Notification.created_at.desc())\
             .limit(limit).all()

def count_unread(db: Session, user: User):
    """Counts unread notifications."""
    count = db.query(models.Notification)\
              .filter(models.Notification.recipient_id == user.id, models.Notification.is_read == False)\
              .count()
    return {"count": count}

def mark_as_read(db: Session, user: User, notification_id: int):
    """Marks a single notification as read."""
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
    """Marks all notifications for the user as read."""
    db.query(models.Notification)\
      .filter(models.Notification.recipient_id == user.id, models.Notification.is_read == False)\
      .update({models.Notification.is_read: True}, synchronize_session=False)
    
    db.commit()
    return {"status": "success"}

# --- D. Unified Sender (The "Smart" Function) ---
async def send_smart_notification(
    db: Session,
    recipient_ids: List[int],
    title: str,
    body: str,
    background_tasks: BackgroundTasks,
    entity_type: str = "general",
    entity_id: int = None,
    click_url: str = "/",
    actor_id: int = None
):
    # 0. Deduplicate
    valid_ids = list(set(recipient_ids))
    if not valid_ids:
        return

    # 1. Bulk DB Insert
    new_notifs = []
    for uid in valid_ids:
        new_notifs.append(models.Notification(
            recipient_id=uid,
            actor_id=actor_id,
            title=title,
            body=body,
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
        "link": click_url,
        "entity_id": str(entity_id)
    }

    for uid in valid_ids:
        await ws_manager.broadcast_personal(
            {"type": "new_notification", "data": ws_payload}, 
            uid
        )

    # 3. Mobile Push (Background)
    devices = db.query(models.UserDevice).filter(models.UserDevice.user_id.in_(valid_ids)).all()
    if devices:
        tokens = [d.fcm_token for d in devices]
        fcm_data = {
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "route": click_url,
            "entity_id": str(entity_id) if entity_id else ""
        }
        background_tasks.add_task(_send_fcm_background, tokens, title, body, fcm_data)

    return True