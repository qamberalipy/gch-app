# app/announcement/service.py
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.announcement.models import Announcement, AnnouncementAttachment, AnnouncementReaction, AnnouncementView
from app.announcement.schema import AnnouncementCreate
from app.user.models import User, UserRole
import re
from typing import Optional

# ... [Keep your existing helper functions: extract_url, fetch_url_metadata] ...
def extract_url(text: str):
    url_regex = r'(https?://[^\s]+)'
    match = re.search(url_regex, text)
    return match.group(0) if match else None

def fetch_url_metadata(url: str):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'} # Simplified for brevity
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code != 200: return {"link_url": url}
        soup = BeautifulSoup(response.content, "html.parser")
        title = soup.find("meta", property="og:title")
        description = soup.find("meta", property="og:description")
        image = soup.find("meta", property="og:image")
        return {
            "link_title": title["content"] if title else (soup.title.string if soup.title else None),
            "link_description": description["content"] if description else None,
            "link_image": image["content"] if image else None,
            "link_url": url
        }
    except Exception:
        return {"link_url": url}

# --- Service Logic ---

# --- REPLACE THIS FUNCTION ---
def get_feed(db: Session, last_id: Optional[int] = None, limit: int = 20):
    """
    Fetches posts using Cursor Pagination.
    - If last_id is provided, fetches posts with ID < last_id (Older posts).
    - Always orders by ID DESC (Newest first).
    """
    query = db.query(Announcement)\
        .options(
            joinedload(Announcement.author),
            joinedload(Announcement.attachments),
            joinedload(Announcement.reactions)
        )
    
    # Cursor Logic: Get older messages
    if last_id:
        query = query.filter(Announcement.id < last_id)
        
    return query.order_by(Announcement.id.desc())\
                .limit(limit)\
                .all()

def create_announcement(db: Session, data: AnnouncementCreate, current_user: User):
    if current_user.role not in [UserRole.admin, UserRole.manager]:
        raise HTTPException(status_code=403, detail="Only Admins and Managers can post announcements.")

    try:
        announcement_data = {
            "author_id": current_user.id,
            "content": data.content
        }

        if data.content:
            url = extract_url(data.content)
            if url:
                metadata = fetch_url_metadata(url)
                announcement_data.update(metadata)

        new_announcement = Announcement(**announcement_data)
        db.add(new_announcement)
        db.flush() 

        for file in data.attachments:
            attachment = AnnouncementAttachment(announcement_id=new_announcement.id, **file.dict())
            db.add(attachment)

        db.commit()
        db.refresh(new_announcement)
        return new_announcement
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")

def delete_announcement(db: Session, announcement_id: int, current_user: User):
    post = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    if current_user.role != UserRole.admin and post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this post.")

    try:
        db.delete(post)
        db.commit()
        return {"status": "deleted", "id": announcement_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete post: {str(e)}")

def mark_as_viewed(db: Session, announcement_id: int, current_user: User):
    exists = db.query(AnnouncementView).filter_by(announcement_id=announcement_id, user_id=current_user.id).first()
    if exists: return {"status": "already_viewed"}
    try:
        view = AnnouncementView(announcement_id=announcement_id, user_id=current_user.id)
        db.add(view)
        db.commit()
        return {"status": "viewed"}
    except Exception:
        db.rollback()
        # Silent fail is okay for view counting
        return {"status": "error"}

def toggle_reaction(db: Session, announcement_id: int, emoji: str, current_user: User):
    try:
        existing = db.query(AnnouncementReaction).filter_by(announcement_id=announcement_id, user_id=current_user.id).first()
        if existing:
            if existing.emoji == emoji: db.delete(existing)
            else: existing.emoji = emoji
        else:
            db.add(AnnouncementReaction(announcement_id=announcement_id, user_id=current_user.id, emoji=emoji))
        db.commit()
        return {"status": "success"}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Reaction failed")

def get_post_viewers(db: Session, announcement_id: int):
    return db.query(AnnouncementView).options(joinedload(AnnouncementView.user)).filter(AnnouncementView.announcement_id == announcement_id).all()