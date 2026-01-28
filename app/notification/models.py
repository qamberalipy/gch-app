# app/notification/models.py
import sqlalchemy as _sql
from sqlalchemy.orm import relationship
import app.core.db.session as _database
from app.user.models import User # Import to link relationships

class Notification(_database.Base):
    __tablename__ = "notification"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    recipient_id = _sql.Column(_sql.Integer, _sql.ForeignKey("user.id"), nullable=False, index=True)
    actor_id = _sql.Column(_sql.Integer, _sql.ForeignKey("user.id"), nullable=True) # Who caused this?
    
    title = _sql.Column(_sql.String(255), nullable=False)
    body = _sql.Column(_sql.Text, nullable=True)
    
    # Navigation Data
    entity_type = _sql.Column(_sql.String(50), nullable=True) # e.g. "task", "invoice"
    entity_id = _sql.Column(_sql.Integer, nullable=True)      # e.g. 105
    click_action_link = _sql.Column(_sql.String(500), nullable=True) # e.g. "/task/105"

    is_read = _sql.Column(_sql.Boolean, default=False)
    created_at = _sql.Column(_sql.DateTime(timezone=True), server_default=_sql.func.now())

    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_id])
    actor = relationship("User", foreign_keys=[actor_id])

class UserDevice(_database.Base):
    __tablename__ = "user_device"
    
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    user_id = _sql.Column(_sql.Integer, _sql.ForeignKey("user.id"), nullable=False)
    fcm_token = _sql.Column(_sql.String(500), nullable=False, unique=True)
    platform = _sql.Column(_sql.String(20), default="android") # android/ios
    
    updated_at = _sql.Column(_sql.DateTime(timezone=True), onupdate=_sql.func.now())