from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Body, HTTPException
from sqlalchemy.orm import Session
from app.core.db.session import get_db as get_db_shared # Assuming you export this or import from session.py
from app.Shared.dependencies import get_current_user, get_db
from app.Shared.helpers import decode_token
from app.notification import service, models
from app.user.models import User

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

# --- 1. WebSocket Endpoint ---
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    # Manual Cookie Auth (Same as your Announcement logic)
    token = websocket.cookies.get("access_token")
    user_id = None
    
    if token:
        try:
            if token.startswith("Bearer "): token = token.split(" ")[1]
            payload = decode_token(token)
            user_id = payload.get("sub") or payload.get("user_id")
        except:
            pass
            
    if not user_id:
        await websocket.close(code=1008)
        return

    await service.ws_manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text() # Keep alive
    except WebSocketDisconnect:
        service.ws_manager.disconnect(websocket, user_id)

# --- 2. REST Endpoints ---
@router.post("/device/token")
def register_device(
    token: str = Body(..., embed=True),
    platform: str = Body("android", embed=True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Called by Flutter app on startup"""
    existing = db.query(models.UserDevice).filter(models.UserDevice.fcm_token == token).first()
    if existing:
        existing.user_id = user.id # Update owner if changed
    else:
        new_device = models.UserDevice(user_id=user.id, fcm_token=token, platform=platform)
        db.add(new_device)
    db.commit()
    return {"message": "Device registered"}

@router.get("/")
def get_notifications(
    limit: int = 20, 
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """Fetch history for the Bell Icon"""
    return db.query(models.Notification)\
             .filter(models.Notification.recipient_id == user.id)\
             .order_by(models.Notification.created_at.desc())\
             .limit(limit).all()

@router.get("/unread-count")
def get_unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = db.query(models.Notification)\
              .filter(models.Notification.recipient_id == user.id, models.Notification.is_read == False)\
              .count()
    return {"count": count}

@router.put("/{id}/read")
def mark_read(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    notif = db.query(models.Notification).filter(models.Notification.id == id, models.Notification.recipient_id == user.id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "ok"}