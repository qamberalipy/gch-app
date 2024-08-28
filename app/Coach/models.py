import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import datetime as _dt
from enum import Enum as PyEnum

class CoachStatus(PyEnum):
    active='active'
    inactive='inactive'
    pending='pending'

class Coach(_database.Base):
    __tablename__ = "coach"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    wallet_address = _sql.Column(_sql.String)
    profile_img = _sql.Column(_sql.String(150))
    first_name = _sql.Column(_sql.String, nullable=True)
    last_name = _sql.Column(_sql.String, nullable=True)
    dob = _sql.Column(_sql.Date, nullable=True)
    gender = _sql.Column(_sql.String(10))
    email = _sql.Column(_sql.String, nullable=True)
    password = _sql.Column(_sql.String(250))
    phone = _sql.Column(_sql.String(20))
    mobile_number = _sql.Column(_sql.String(20))
    notes = _sql.Column(_sql.String)
    source_id = _sql.Column(_sql.Integer)
    country_id = _sql.Column(_sql.Integer)
    city = _sql.Column(_sql.String(20))
    zipcode = _sql.Column(_sql.String(10))
    address_1 = _sql.Column(_sql.String(100))
    address_2 = _sql.Column(_sql.String(100))
    last_online = _sql.Column(_sql.DateTime)
    bank_detail_id = _sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime)
    updated_at = _sql.Column(_sql.DateTime)
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted = _sql.Column(_sql.Boolean, default=False)

class CoachOrganization(_database.Base):
    __tablename__ = "coach_organization"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    coach_id = _sql.Column(_sql.Integer)
    check_in = _sql.Column(_sql.DateTime)
    own_coach_id = _sql.Column(_sql.String, nullable=True)
    org_id = _sql.Column(_sql.Integer)
    coach_status = _sql.Column(_sql.Enum(CoachStatus))
    is_deleted = _sql.Column(_sql.Boolean, default=False)
