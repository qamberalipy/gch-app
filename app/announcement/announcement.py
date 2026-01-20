# app/announcement/announcement.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload
import app.core.db.session as _database
import app.user.user as _user_auth
from app.announcement import service, schema

def get_db():
    db = _database.SessionLocal()
    try: yield db
    finally: db.close()

router = APIRouter()

@router.post("/", response_model=schema.AnnouncementResponse)
def create_post(
    data: schema.AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user = Depends(_user_auth.get_current_user)
):
    return service.create_announcement(db, data, current_user)

@router.get("/", response_model=list[schema.AnnouncementResponse])
def get_feed(
    skip: int = 0, 
    limit: int = 20, 
    db: Session = Depends(get_db),
    current_user = Depends(_user_auth.get_current_user)
):
    # OPTIMIZED QUERY: Using joinedload and selectinload to fetch everything in 1 query
    return db.query(service.Announcement)\
        .options(
            joinedload(service.Announcement.author),       # Fetch Author immediately
            selectinload(service.Announcement.attachments), # Fetch Attachments efficiently
            selectinload(service.Announcement.reactions),   # Fetch Reactions efficiently
            selectinload(service.Announcement.views)        # Fetch Views for count
        )\
        .order_by(service.Announcement.created_at.desc())\
        .offset(skip).limit(limit).all()

@router.delete("/{id}")
def delete_post(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(_user_auth.get_current_user)
):
    return service.delete_announcement(db, id, current_user)

@router.post("/{id}/react")
def react_to_post(
    id: int, 
    reaction: schema.ReactionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(_user_auth.get_current_user)
):
    return service.toggle_reaction(db, id, reaction.emoji, current_user)

@router.post("/{id}/view")
def mark_viewed(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(_user_auth.get_current_user)
):
    return service.mark_as_viewed(db, id, current_user)

@router.get("/{id}/viewers", response_model=list[schema.ViewerResponse])
def get_viewers(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(_user_auth.get_current_user)
):
    # Ideally restrict this to Admins/Managers only
    if current_user.role not in ["admin", "manager"]:
         raise HTTPException(status_code=403, detail="Not authorized to see viewers")
    return service.get_post_viewers(db, id)