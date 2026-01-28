import firebase_admin
from firebase_admin import messaging, credentials
from sqlalchemy.orm import Session
from fastapi import WebSocket
from typing import List, Dict

from app.notification.models import Notification, UserDevice
from app.user.models import User

# --- A. WebSocket Manager (Copied & Adapted from your Announcement logic) ---
class NotificationManager:
    def __init__(self):
        # Map user_id -> List[WebSocket] (User might have multiple tabs open)
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

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            # Send to all open tabs for this user
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Clean up dead connections
                    self.disconnect(connection, user_id)

ws_manager = NotificationManager()

# --- B. Unified Send Function ---
async def send_notification(
    db: Session,
    recipient_id: int,
    title: str,
    body: str,
    entity_type: str = "general",
    entity_id: int = None,
    click_url: str = "/",
    actor_id: int = None
):
    """
    1. Saves to DB
    2. Pushes to Web Socket
    3. Pushes to Mobile FCM
    """
    # 1. Save to DB
    new_notif = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        title=title,
        body=body,
        entity_type=entity_type,
        entity_id=entity_id,
        click_action_link=click_url
    )
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)

    # 2. Web Real-time (WebSocket)
    payload = {
        "id": new_notif.id,
        "title": title,
        "body": body,
        "link": click_url,
        "created_at": str(new_notif.created_at)
    }
    await ws_manager.send_personal_message({"type": "new_notification", "data": payload}, recipient_id)

    # 3. Mobile Push (FCM)
    devices = db.query(UserDevice).filter(UserDevice.user_id == recipient_id).all()
    if devices:
        tokens = [d.fcm_token for d in devices]
        
        # We send 'data' payload for Flutter handler
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={
                "click_action": "FLUTTER_NOTIFICATION_CLICK",
                "route": click_url,
                "entity_id": str(entity_id) if entity_id else ""
            },
            tokens=tokens
        )
        try:
            messaging.send_multicast(message)
        except Exception as e:
            print(f"FCM Error: {e}")

    return new_notif