
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative
from enum import Enum as PyEnum

class RecurrencyEnum(PyEnum):
    daily = "daily"
    weekly = "weekly"
    yearly = "yearly"
    monthly = "monthly"

class StatusEnum(PyEnum):
    pending = "pending"
    inprogress = "In Progress"
    completed = "completed"

class Events(_database.Base):
    __tablename__ = 'events'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    activity = _sql.Column(_sql.String(100), nullable=False)
    org_id = _sql.Column(_sql.Integer, nullable=True)
    coach_id = _sql.Column(_sql.Integer, nullable=True)
    price=_sql.Column(_sql.Float, nullable=True)
    description = _sql.Column(_sql.Text, nullable=True)
    recurrency = _sql.Column(_sql.Enum(RecurrencyEnum), nullable=True)
    link = _sql.Column(_sql.String(50), nullable=True)
    notes = _sql.Column(_sql.Text, nullable=True)
    credit_type = _sql.Column(_sql.String(50), nullable=True)
    start_time = _sql.Column(_sql.DateTime, nullable=False)
    participants = _sql.Column(_sql.String(100), nullable=True)
    end_time = _sql.Column(_sql.DateTime, nullable=False)
    created_at = _sql.Column(_sql.DateTime, server_default=_sql.func.now())
    created_by = _sql.Column(_sql.Integer, nullable=False)
    updated_at = _sql.Column(_sql.DateTime, server_default=_sql.func.now(), onupdate=_sql.func.now())
    updated_by = _sql.Column(_sql.Integer, nullable=True)
    status = _sql.Column(_sql.Enum(StatusEnum), nullable=False)
    is_deleted = _sql.Column(_sql.Boolean, default=0)
